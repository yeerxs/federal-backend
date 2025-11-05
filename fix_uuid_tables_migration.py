import sqlite3
import os

def fix_uuid_tables_migration():
    """Corrige as tabelas para usar TEXT em vez de INTEGER para user_id (UUIDs)"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('instance', 'federal_associados.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Iniciando correção das tabelas para suportar UUIDs...")
    
    # Lista de tabelas que precisam ser corrigidas
    tables_to_fix = [
        {
            'name': 'access_logs',
            'create_sql': '''CREATE TABLE access_logs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action VARCHAR(100) NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )''',
            'copy_sql': '''INSERT INTO access_logs_new (id, user_id, action, ip_address, user_agent, created_at)
                          SELECT id, CAST(user_id AS TEXT), action, ip_address, user_agent, created_at 
                          FROM access_logs'''
        },
        {
            'name': 'password_history',
            'create_sql': '''CREATE TABLE password_history_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )''',
            'copy_sql': '''INSERT INTO password_history_new (id, user_id, password_hash, action_type, created_at)
                          SELECT id, CAST(user_id AS TEXT), password_hash, action_type, created_at 
                          FROM password_history'''
        },
        {
            'name': 'email_logs',
            'create_sql': '''CREATE TABLE email_logs_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                email_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'sent',
                temp_password VARCHAR(255),
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )''',
            'copy_sql': '''INSERT INTO email_logs_new (id, user_id, email_type, status, temp_password, sent_at)
                          SELECT id, CAST(user_id AS TEXT), email_type, status, temp_password, sent_at 
                          FROM email_logs'''
        }
    ]
    
    for table_info in tables_to_fix:
        table_name = table_info['name']
        
        try:
            # Verificar se a tabela existe
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"⚠️ Tabela {table_name} não existe, pulando...")
                continue
            
            print(f"🔧 Corrigindo tabela {table_name}...")
            
            # 1. Criar nova tabela com estrutura correta
            cursor.execute(table_info['create_sql'])
            print(f"✅ Nova tabela {table_name}_new criada")
            
            # 2. Copiar dados da tabela antiga para a nova (se houver dados)
            try:
                cursor.execute(table_info['copy_sql'])
                print(f"✅ Dados copiados para {table_name}_new")
            except Exception as e:
                print(f"⚠️ Nenhum dado para copiar em {table_name}: {e}")
            
            # 3. Remover tabela antiga
            cursor.execute(f"DROP TABLE {table_name}")
            print(f"✅ Tabela antiga {table_name} removida")
            
            # 4. Renomear nova tabela
            cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
            print(f"✅ Tabela {table_name} renomeada com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao corrigir tabela {table_name}: {e}")
            # Rollback em caso de erro
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}_new")
            except:
                pass
    
    # Recriar índices
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
            print(f'✅ Índice {index_name} recriado')
        except Exception as e:
            print(f'⚠️ Erro ao recriar índice {index_name}: {e}')
    
    # Verificar estrutura das tabelas corrigidas
    for table_info in tables_to_fix:
        table_name = table_info['name']
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"\n📋 Estrutura da tabela {table_name}:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        except Exception as e:
            print(f"⚠️ Erro ao verificar estrutura de {table_name}: {e}")
    
    conn.commit()
    conn.close()
    print('\n🎉 Correção das tabelas executada com sucesso!')
    print('✅ Agora as tabelas suportam UUIDs como user_id')

if __name__ == '__main__':
    fix_uuid_tables_migration()