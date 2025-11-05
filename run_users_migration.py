#!/usr/bin/env python3
"""
Script para atualizar a tabela users com as colunas necessárias
Federal Associados - Sistema de Login e Primeiro Acesso
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def run_users_migration():
    """Executa a migração para atualizar a tabela users"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('federal_system.db')
    if not os.path.exists(db_path):
        db_path = os.path.join('instance', 'federal_system.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Iniciando migração da tabela users...")
    
    try:
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Adicionar colunas se não existirem
        new_columns = [
            ("cpf", "VARCHAR(11) UNIQUE"),
            ("status", "VARCHAR(20) DEFAULT 'pending'"),
            ("first_access_completed", "BOOLEAN DEFAULT FALSE"),
            ("password_created_at", "TIMESTAMP"),
            ("type", "VARCHAR(20) DEFAULT 'user'")
        ]
        
        for col_name, col_def in new_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                    print(f"✅ Coluna '{col_name}' adicionada com sucesso")
                except Exception as e:
                    print(f"⚠️ Aviso ao adicionar coluna '{col_name}': {e}")
            else:
                print(f"✅ Coluna '{col_name}' já existe")
        
        # Criar índices
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf)",
            "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
            "CREATE INDEX IF NOT EXISTS idx_users_type ON users(type)"
        ]
        
        for index_sql in indices:
            try:
                cursor.execute(index_sql)
                print(f"✅ Índice criado: {index_sql.split()[-1]}")
            except Exception as e:
                print(f"⚠️ Aviso ao criar índice: {e}")
        
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
                    first_access_completed = TRUE,
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
                True,
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
        
        print("\n🎉 Migração da tabela users concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    run_users_migration()