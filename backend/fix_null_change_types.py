import sqlite3
import os
from datetime import datetime

# Garante que o caminho do banco seja relativo ao script
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(script_dir, "inventory.db")

def fix_null_change_types():
    """
    Atualiza todos os registros com change_type NULL para 'modified'
    baseado na análise das descrições.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Primeiro, criar backup antes de fazer alterações
        backup_path = DB_PATH + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Criando backup em: {backup_path}")
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        print("Backup criado com sucesso!")
        
        # Contar registros com change_type NULL
        cursor.execute("SELECT COUNT(*) FROM history_logs WHERE change_type IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"\nEncontrados {null_count} registros com change_type NULL")
        
        if null_count == 0:
            print("Nenhum registro para corrigir!")
            return
        
        # Analisar as descrições para determinar o tipo correto
        cursor.execute("SELECT id, change_description FROM history_logs WHERE change_type IS NULL")
        rows = cursor.fetchall()
        
        updates = []
        for row_id, desc in rows:
            # Determinar o tipo baseado na descrição
            if desc:
                desc_lower = desc.lower()
                if "adicionado" in desc_lower or "criado" in desc_lower or "novo" in desc_lower:
                    change_type = "added"
                elif "removido" in desc_lower or "deletado" in desc_lower or "excluído" in desc_lower:
                    change_type = "removed"
                elif "substituído" in desc_lower or "trocado" in desc_lower:
                    change_type = "replaced"
                else:
                    # Para mudanças de valores (maioria dos casos)
                    change_type = "modified"
            else:
                # Se não há descrição, assumir modified
                change_type = "modified"
            
            updates.append((change_type, row_id))
        
        # Aplicar as atualizações
        print("\nAtualizando registros...")
        cursor.executemany("UPDATE history_logs SET change_type = ? WHERE id = ?", updates)
        conn.commit()
        
        print(f"[OK] {len(updates)} registros atualizados com sucesso!")
        
        # Verificar se ainda há NULLs
        cursor.execute("SELECT COUNT(*) FROM history_logs WHERE change_type IS NULL")
        remaining_nulls = cursor.fetchone()[0]
        
        if remaining_nulls == 0:
            print("[OK] Todos os registros foram corrigidos!")
        else:
            print(f"[AVISO] Ainda restam {remaining_nulls} registros com change_type NULL")
        
        # Mostrar estatísticas dos tipos atribuídos
        print("\nEstatísticas dos tipos atribuídos:")
        type_counts = {}
        for change_type, _ in updates:
            type_counts[change_type] = type_counts.get(change_type, 0) + 1
        
        for change_type, count in sorted(type_counts.items()):
            print(f"  {change_type}: {count} registros")
        
    except Exception as e:
        print(f"Erro ao corrigir registros: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_null_change_types()
