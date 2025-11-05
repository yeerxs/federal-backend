import sqlite3
import os

def run_cpf_migration():
    """Executa a migration para o sistema de autenticação por CPF"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('instance', 'federal_associados.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Iniciando migration do sistema de autenticação por CPF...")
    
    # 1. Verificar se a coluna status já existe
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'new'")
        print('✅ Coluna status adicionada')
    except Exception as e:
        print(f'⚠️ Coluna status já existe: {e}')
    
    # 2. Criar tabelas que ainda não existem
    tables_to_create = [
        {
            'name': 'password_history',
            'sql': '''CREATE TABLE IF NOT EXISTS password_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )'''
        },
        {
            'name': 'email_logs',
            'sql': '''CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'sent',
                temp_password VARCHAR(255),
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )'''
        },
        {
            'name': 'access_logs',
            'sql': '''CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action VARCHAR(100) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )'''
        }
    ]
    
    for table in tables_to_create:
        try:
            cursor.execute(table['sql'])
            print(f'✅ Tabela {table["name"]} criada')
        except Exception as e:
            print(f'⚠️ Erro ao criar tabela {table["name"]}: {e}')
    
    # 3. Criar índices
    indices = [
        ('idx_users_status', 'CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)'),
        ('idx_users_cpf', 'CREATE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf)'),
        ('idx_password_history_user_id', 'CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON password_history(user_id)'),
        ('idx_email_logs_user_id', 'CREATE INDEX IF NOT EXISTS idx_email_logs_user_id ON email_logs(user_id)'),
        ('idx_access_logs_user_id', 'CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id)')
    ]
    
    for index_name, index_sql in indices:
        try:
            cursor.execute(index_sql)
            print(f'✅ Índice {index_name} criado')
        except Exception as e:
            print(f'⚠️ Erro ao criar índice {index_name}: {e}')
    
    # 4. Inserir dados de teste
    test_data = [
        ('12345678901', 'cliente1@example.com', 'Cliente Teste 1', 'new', 1),
        ('98765432100', 'cliente2@example.com', 'Cliente Teste 2', 'active', 1),
        ('11122233344', 'cliente3@example.com', 'Cliente Teste 3', 'reactivation', 1)
    ]
    
    for cpf, email, name, status, is_active in test_data:
        try:
            cursor.execute('INSERT OR IGNORE INTO users (cpf, email, name, status, is_active) VALUES (?, ?, ?, ?, ?)', 
                          (cpf, email, name, status, is_active))
            print(f'✅ Usuário teste inserido: {cpf}')
        except Exception as e:
            print(f'⚠️ Erro ao inserir usuário {cpf}: {e}')
    
    # 5. Verificar estrutura das tabelas
    cursor.execute("PRAGMA table_info(users)")
    users_columns = cursor.fetchall()
    print(f"\n📋 Colunas da tabela users: {[col[1] for col in users_columns]}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%password%' OR name LIKE '%email%' OR name LIKE '%access%'")
    new_tables = cursor.fetchall()
    print(f"📋 Novas tabelas criadas: {[table[0] for table in new_tables]}")
    
    conn.commit()
    conn.close()
    print('🎉 Migration executada com sucesso!')

if __name__ == '__main__':
    run_cpf_migration()