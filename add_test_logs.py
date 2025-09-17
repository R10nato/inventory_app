import sqlite3
from datetime import datetime

# Conectar ao banco
conn = sqlite3.connect('backend/inventory.db')
cursor = conn.cursor()

# Adicionar alguns logs de teste com change_type preenchido
test_logs = [
    (1, 'cpu', 'added', 'CPU adicionado ao sistema', 'Intel Core i5', 'Intel Core i7', datetime.now().isoformat()),
    (1, 'memory', 'modified', 'Memória RAM atualizada', '8GB', '16GB', datetime.now().isoformat()),
    (1, 'disk', 'removed', 'Disco removido do sistema', 'HDD 500GB', None, datetime.now().isoformat()),
]

for log in test_logs:
    cursor.execute('''
        INSERT INTO history_logs (device_id, component, change_type, change_description, details_before, details_after, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', log)

conn.commit()
print(f'Adicionados {len(test_logs)} logs de teste')

# Verificar
cursor.execute('SELECT COUNT(*) FROM history_logs WHERE device_id = 1 AND change_type IS NOT NULL')
count = cursor.fetchone()[0]
print(f'Total de logs com change_type preenchido: {count}')

conn.close()
