import sqlite3
import os

# Garante que o caminho do banco seja relativo ao script
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(script_dir, "inventory.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Verificar se ainda existem registros com change_type NULL
print("Verificando registros com change_type NULL:")
cursor.execute("SELECT COUNT(*) FROM history_logs WHERE change_type IS NULL")
null_count = cursor.fetchone()[0]
print(f"  Registros com change_type NULL: {null_count}")

# Verificar a distribuição dos tipos
print("\nDistribuição dos tipos de mudança:")
cursor.execute("SELECT change_type, COUNT(*) FROM history_logs GROUP BY change_type")
rows = cursor.fetchall()
for change_type, count in rows:
    print(f"  {change_type}: {count} registros")

# Verificar alguns registros de exemplo
print("\nPrimeiros 5 registros:")
cursor.execute("SELECT id, device_id, change_type, change_description FROM history_logs LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    desc = row[3][:50] + "..." if row[3] and len(row[3]) > 50 else row[3]
    print(f"  ID {row[0]}: device_id={row[1]}, type={row[2]}, desc={desc}")

conn.close()
print("\nVerificação concluída!")
