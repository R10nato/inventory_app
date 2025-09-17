"""
Script de migração para adicionar colunas faltantes na tabela history_logs.
Execute este script para atualizar o banco de dados existente.
"""

import sqlite3
import json
from datetime import datetime
import os
import shutil

def backup_database(db_path):
    """Cria um backup do banco de dados antes da migração."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"[OK] Backup criado: {backup_path}")
    return backup_path

def check_column_exists(cursor, table_name, column_name):
    """Verifica se uma coluna existe na tabela."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
    """Adiciona uma coluna se ela não existir."""
    if not check_column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            print(f"  [OK] Coluna '{column_name}' adicionada")
            return True
        except sqlite3.OperationalError as e:
            print(f"  [AVISO] Erro ao adicionar coluna '{column_name}': {e}")
            return False
    else:
        print(f"  [INFO] Coluna '{column_name}' ja existe")
        return False

def migrate_history_logs(db_path="inventory.db"):
    """Executa a migração da tabela history_logs."""
    
    # Criar backup
    print("\n[INICIANDO] Migracao da tabela history_logs...")
    backup_path = backup_database(db_path)
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n[PROCESSANDO] Adicionando colunas faltantes na tabela history_logs...")
        
        # Lista de colunas para adicionar
        columns_to_add = [
            ("change_hash", "VARCHAR(64)"),
            ("change_type", "VARCHAR(50)"),
            ("path", "VARCHAR(500)"),
            ("old_value", "JSON"),
            ("new_value", "JSON"),
            ("evidence", "JSON"),
            ("agent_version", "VARCHAR(50)")
        ]
        
        # Adicionar cada coluna
        added_count = 0
        for column_name, column_type in columns_to_add:
            if add_column_if_not_exists(cursor, "history_logs", column_name, column_type):
                added_count += 1
        
        # Criar índices se não existirem
        print("\n[INDICES] Criando indices...")
        
        # Verificar e criar índices
        indices = [
            ("idx_device_change_hash", "CREATE INDEX IF NOT EXISTS idx_device_change_hash ON history_logs(device_id, change_hash)"),
            ("idx_device_timestamp", "CREATE INDEX IF NOT EXISTS idx_device_timestamp ON history_logs(device_id, timestamp)"),
            ("idx_change_type", "CREATE INDEX IF NOT EXISTS idx_change_type ON history_logs(change_type)")
        ]
        
        for idx_name, idx_sql in indices:
            try:
                cursor.execute(idx_sql)
                print(f"  [OK] Indice '{idx_name}' criado/verificado")
            except sqlite3.OperationalError as e:
                print(f"  [AVISO] Erro com indice '{idx_name}': {e}")
        
        # Commit das mudanças
        conn.commit()
        
        # Verificar estrutura final
        print("\n[ESTRUTURA] Estrutura final da tabela history_logs:")
        cursor.execute("PRAGMA table_info(history_logs)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Fechar conexão
        conn.close()
        
        print(f"\n[SUCESSO] Migracao concluida com sucesso!")
        print(f"   {added_count} colunas adicionadas")
        
        if added_count == 0:
            print("   [INFO] Todas as colunas ja existiam")
        
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Erro durante a migracao: {e}")
        print(f"   Restaure o backup se necessário: {backup_path}")
        return False

def verify_migration(db_path="inventory.db"):
    """Verifica se a migração foi bem-sucedida."""
    print("\n[VERIFICANDO] Verificando migracao...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar colunas essenciais
        required_columns = ["change_hash", "change_type", "path", "old_value", "new_value", "evidence", "agent_version"]
        
        cursor.execute("PRAGMA table_info(history_logs)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        missing = [col for col in required_columns if col not in existing_columns]
        
        if missing:
            print(f"[ERRO] Colunas faltando: {', '.join(missing)}")
            return False
        else:
            print("[OK] Todas as colunas necessarias estao presentes")
            
        # Testar inserção
        print("\n[TESTE] Testando insercao...")
        try:
            cursor.execute("""
                INSERT INTO history_logs (
                    device_id, component, change_description, 
                    change_type, path, old_value, new_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                999999,  # device_id temporário para teste
                "test", 
                "Teste de migração",
                "modified",
                "test.path",
                json.dumps({"test": "old"}),
                json.dumps({"test": "new"})
            ))
            
            # Remover registro de teste
            cursor.execute("DELETE FROM history_logs WHERE device_id = 999999")
            conn.commit()
            print("[OK] Insercao de teste bem-sucedida")
            
        except Exception as e:
            print(f"[ERRO] Erro na insercao de teste: {e}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro na verificacao: {e}")
        return False

if __name__ == "__main__":
    # Executar migração
    success = migrate_history_logs()
    
    if success:
        # Verificar migração
        verify_migration()
        print("\n[COMPLETO] Migracao completa! O banco de dados esta pronto para uso.")
    else:
        print("\n[FALHOU] Migracao falhou. Verifique os erros acima.")
