#!/usr/bin/env python3
"""
Migração para adicionar Super Admin e sistema de permissões
"""

import sqlite3
import os
import uuid
from datetime import datetime

def run_migration():
    # Conectar ao banco SQLite
    db_path = 'instance/federal_system.db'
    print(f'Verificando banco em: {db_path}')
    print(f'Existe: {os.path.exists(db_path)}')

    if not os.path.exists(db_path):
        print('Banco de dados não encontrado!')
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar tabelas existentes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print('Tabelas existentes:', [t[0] for t in tables])
        
        # Verificar se a tabela users existe
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        result = cursor.fetchone()
        
        if not result:
            print('Tabela users não encontrada')
            return False
            
        print('Estrutura da tabela users encontrada')
        
        # 1. Criar tabela de permissões
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print('Tabela permissions criada')
        
        # 2. Criar tabela user_permissions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_permissions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            permission_id TEXT NOT NULL,
            granted_by TEXT,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
            FOREIGN KEY (granted_by) REFERENCES users(id),
            UNIQUE(user_id, permission_id)
        )
        ''')
        print('Tabela user_permissions criada')
        
        # 3. Inserir permissões básicas
        permissions = [
            ('manage_users', 'Criar, editar e excluir usuários', 'users'),
            ('view_users', 'Visualizar lista de usuários', 'users'),
            ('reset_user_passwords', 'Resetar senhas de usuários', 'users'),
            ('toggle_user_first_access', 'Forçar/remover primeiro acesso de usuários', 'users'),
            ('manage_user_permissions', 'Gerenciar permissões de outros usuários', 'users'),
            ('manage_activations', 'Aprovar, reprovar e gerenciar ativações', 'activations'),
            ('view_activations', 'Visualizar ativações', 'activations'),
            ('send_qr_codes', 'Enviar QR codes para ativações', 'activations'),
            ('view_activation_statistics', 'Visualizar estatísticas de ativações', 'activations'),
            ('manage_ddds', 'Criar, editar e excluir DDDs', 'ddds'),
            ('view_ddds', 'Visualizar DDDs disponíveis', 'ddds'),
            ('view_admin_dashboard', 'Acessar dashboard administrativo', 'dashboard'),
            ('view_detailed_statistics', 'Visualizar estatísticas detalhadas com gráficos', 'dashboard'),
            ('view_admin_logs', 'Visualizar logs administrativos', 'system'),
            ('manage_system_settings', 'Gerenciar configurações do sistema', 'system')
        ]
        
        inserted_count = 0
        for name, desc, category in permissions:
            perm_id = str(uuid.uuid4())
            try:
                cursor.execute('''
                INSERT OR IGNORE INTO permissions (id, name, description, category) 
                VALUES (?, ?, ?, ?)
                ''', (perm_id, name, desc, category))
                if cursor.rowcount > 0:
                    inserted_count += 1
            except Exception as e:
                print(f'Erro ao inserir permissão {name}: {e}')
        
        print(f'Permissões inseridas: {inserted_count}')
        
        # 4. Criar índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_permissions_permission_id ON user_permissions(permission_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_permissions_category ON permissions(category)')
        print('Índices criados')
        
        # 5. Verificar se existem usuários admin para criar um super_admin
        cursor.execute("SELECT id, email, name FROM users WHERE user_type = 'admin' LIMIT 1")
        admin_user = cursor.fetchone()
        
        if admin_user:
            # Criar um super admin baseado no primeiro admin
            super_admin_id = str(uuid.uuid4())
            admin_id, admin_email, admin_name = admin_user
            
            # Criar super admin com email diferente
            super_admin_email = f"super_{admin_email}"
            
            cursor.execute('''
            INSERT OR IGNORE INTO users (
                id, cpf, email, password_hash, user_type, name, 
                created_at, updated_at, is_active, first_access_completed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                super_admin_id, 
                '00000000000',  # CPF temporário
                super_admin_email,
                '$2b$12$dummy_hash_for_super_admin',  # Hash temporário
                'super_admin',
                f'Super {admin_name}',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                1,
                1
            ))
            
            if cursor.rowcount > 0:
                print(f'Super Admin criado: {super_admin_email}')
                
                # Dar todas as permissões ao super admin
                cursor.execute("SELECT id FROM permissions")
                all_permissions = cursor.fetchall()
                
                for perm_id_tuple in all_permissions:
                    perm_id = perm_id_tuple[0]
                    user_perm_id = str(uuid.uuid4())
                    cursor.execute('''
                    INSERT OR IGNORE INTO user_permissions (id, user_id, permission_id, granted_by, is_active)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (user_perm_id, super_admin_id, perm_id, super_admin_id, 1))
                
                print(f'Todas as permissões concedidas ao Super Admin')
        
        conn.commit()
        print('Migração concluída com sucesso!')
        return True
        
    except Exception as e:
        conn.rollback()
        print(f'Erro na migração: {e}')
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = run_migration()
    if success:
        print('\n✅ Migração executada com sucesso!')
    else:
        print('\n❌ Falha na migração!')