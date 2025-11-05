import sqlite3

conn = sqlite3.connect('instance/federal_system.db')
cursor = conn.cursor()

# Verificar tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tabelas:', [t[0] for t in tables])

# Se users_new existe, renomear para users
if 'users_new' in [t[0] for t in tables]:
    print('Renomeando users_new para users...')
    cursor.execute('ALTER TABLE users_new RENAME TO users')
    conn.commit()
    print('Tabela renomeada!')

conn.close()