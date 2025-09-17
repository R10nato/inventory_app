import sqlite3

conn = sqlite3.connect('backend/inventory.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('Tabelas no banco:')
for t in tables:
    print(f'  - {t[0]}')

conn.close()
