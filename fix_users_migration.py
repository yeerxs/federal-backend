#!/usr/bin/env python3
"""
Script para corrigir a migração da tabela users
Federal Associados - Sistema de Login e Primeiro Acesso
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def fix_users_migration():
    """Corrige a migração da tabela users"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('federal_system.db')
    if not os.path.exists(db_path):
        db_path = os.path.join('instance', 'federal_system.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Corrigindo migração da tabela users...")
    
    try:
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Adicionar coluna CPF sem UNIQUE (vamos criar índice depois)
        if 'cpf' not in columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN cpf VARCHAR(11)")
                print("✅ Coluna 'cpf' adicionada com sucesso")
            except Exception as e:
                print(f"⚠️ Aviso ao adicionar coluna 'cpf': {e}")
        else:
            print("✅ Coluna 'cpf' já existe")
        
        # Criar índice único para CPF
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_cpf_unique ON users(cpf)")
            print("✅ Índice único para CPF criado")
        except Exception as e:
            print(f"⚠️ Aviso ao criar índice único para CPF: {e}")
        
        # Verificar se admin existe
        cursor.execute("SELECT id, email FROM users WHERE email = 'admin@federal.com'")
        admin = cursor.fetchone()
        
        if admin:
            # Atualizar admin existente
            admin_id = admin[0]
            password_hash = generate_password_hash('admin123')
            
            cursor.execute("""
                UPDATE users 
                SET cpf = ?, 
                    status = 'active', 
                    first_access_completed = 1,
                    type = 'admin',
                    password_created_at = datetime('now'),
                    password_hash = ?
                WHERE id = ?
            """, ('12345678990', password_hash, admin_id))
            
            print("✅ Admin existente atualizado com sucesso")
        else:
            # Criar admin se não existir
            password_hash = generate_password_hash('admin123')
            
            cursor.execute("""
                INSERT INTO users (
                    email, 
                    password_hash, 
                    name, 
                    role, 
                    cpf, 
                    status, 
                    first_access_completed, 
                    type,
                    password_created_at,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                'admin@federal.com',
                password_hash,
                'Administrador Federal',
                'admin',
                '12345678990',
                'active',
                1,
                'admin'
            ))
            
            print("✅ Admin criado com sucesso")
        
        # Commit das mudanças
        conn.commit()
        
        # Verificar estrutura final
        cursor.execute("PRAGMA table_info(users)")
        final_columns = cursor.fetchall()
        
        print("\n📋 Estrutura final da tabela users:")
        for col in final_columns:
            print(f"  ✅ {col[1]} ({col[2]})")
        
        # Verificar admin
        cursor.execute("""
            SELECT email, cpf, status, type, first_access_completed 
            FROM users WHERE email = 'admin@federal.com'
        """)
        admin_data = cursor.fetchone()
        
        if admin_data:
            print(f"\n👤 Admin configurado:")
            print(f"  Email: {admin_data[0]}")
            print(f"  CPF: {admin_data[1]}")
            print(f"  Status: {admin_data[2]}")
            print(f"  Tipo: {admin_data[3]}")
            print(f"  Primeiro acesso: {admin_data[4]}")
        
        # Verificar todas as tabelas do sistema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tabelas no sistema ({len(tables)}):")
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        print("\n🎉 Correção da migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a correção: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_users_migration()