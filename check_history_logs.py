import sqlite3

# Conectar ao banco
conn = sqlite3.connect('backend/inventory.db')
cursor = conn.cursor()

# Verificar total de logs
cursor.execute('SELECT COUNT(*) FROM history_logs')
total = cursor.fetchone()[0]
print(f'Total de logs no banco: {total}')

# Verificar logs do device 1
cursor.execute('SELECT COUNT(*) FROM history_logs WHERE device_id = 1')
device1_logs = cursor.fetchone()[0]
print(f'Total de logs para device 1: {device1_logs}')

# Mostrar alguns exemplos
cursor.execute('''
    SELECT id, device_id, component, change_type, change_description, timestamp 
    FROM history_logs 
    WHERE device_id = 1 
    LIMIT 5
''')
rows = cursor.fetchall()

if rows:
    print('\nExemplos de logs:')
    for row in rows:
        print(f'  ID: {row[0]}')
        print(f'  Device: {row[1]}')
        print(f'  Component: {row[2]}')
        print(f'  Type: {row[3]}')
        print(f'  Description: {row[4][:50] if row[4] else "N/A"}...')
        print(f'  Time: {row[5]}')
        print('  ---')
else:
    print('\nNenhum log encontrado para device 1')
    
    # Verificar se há logs para outros devices
    cursor.execute('SELECT DISTINCT device_id FROM history_logs LIMIT 5')
    devices = cursor.fetchall()
    if devices:
        print(f'\nDevices com logs: {[d[0] for d in devices]}')

conn.close()
