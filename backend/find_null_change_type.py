import sqlite3
import os

# Garante que o caminho do banco seja relativo ao script
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(script_dir, "inventory.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Buscar registros com change_type NULL
def find_null_change_type():
    print("Registros com change_type NULL:")
    cursor.execute("SELECT id, device_id, change_description FROM history_logs WHERE change_type IS NULL")
    rows = cursor.fetchall()
    for row in rows:
        print(f"id={row[0]}, device_id={row[1]}, desc={row[2]}")
    if not rows:
        print("Nenhum registro com change_type NULL encontrado.")

if __name__ == "__main__":
    find_null_change_type()
    conn.close()
