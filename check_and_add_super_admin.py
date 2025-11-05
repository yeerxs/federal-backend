#!/usr/bin/env python3

import sqlite3
import os
import uuid
from werkzeug.security import generate_password_hash
from datetime import datetime

def check_and_add_super_admin():
    # Caminho para o banco SQLite
    db_path = os.path.join('instance', 'federal_associados.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 Verificando estrutura da tabela users...")
        
        # Verificar estrutura da tabela users
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("📋 Colunas da tabela users:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verificar usuários existentes
        cursor.execute("SELECT id, email, user_type, name FROM users")
        users = cursor.fetchall()
        
        print(f"\n👥 Usuários existentes ({len(users)}):")
        for user in users:
            print(f"  - {user[1]} ({user[2]}) - {user[3]}")
        
        # Verificar se já existe um super_admin
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_type = 'super_admin'")
        super_admin_count = cursor.fetchone()[0]
        
        if super_admin_count > 0:
            print(f"\n✅ Já existem {super_admin_count} super admin(s) no sistema!")
            return True
        
        print("\n🔧 Criando usuário Super Admin...")
        
        # Criar usuário super admin
        super_admin_id = str(uuid.uuid4())
        email = "superadmin@federal.com"
        password_hash = generate_password_hash("admin123")
        name = "Super Administrador"
        
        cursor.execute("""
            INSERT INTO users (
                id, cpf, email, password_hash, user_type, name, 
                created_at, updated_at, is_active, first_access_completed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            super_admin_id,
            "00000000000",  # CPF fictício para super admin
            email,
            password_hash,
            "super_admin",
            name,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            True,
            True
        ))
        
        conn.commit()
        
        print("✅ Super Admin criado com sucesso!")
        print(f"📧 Email: {email}")
        print("🔑 Senha: admin123")
        
        return True
        
    except sqlite3.IntegrityError as e:
        if "CHECK constraint failed" in str(e):
            print("❌ Erro: O tipo 'super_admin' não é permitido no enum user_type")
            print("💡 Será necessário atualizar o schema do banco de dados")
            
            # Tentar atualizar um usuário admin existente para super_admin
            print("\n🔄 Tentando promover um admin existente para super_admin...")
            
            cursor.execute("SELECT id, email FROM users WHERE user_type = 'admin' LIMIT 1")
            admin_user = cursor.fetchone()
            
            if admin_user:
                try:
                    # Primeiro, vamos verificar se podemos alterar o tipo diretamente
                    cursor.execute("UPDATE users SET user_type = 'super_admin' WHERE id = ?", (admin_user[0],))
                    conn.commit()
                    print(f"✅ Usuário {admin_user[1]} promovido para super_admin!")
                    return True
                except Exception as update_error:
                    print(f"❌ Erro ao promover usuário: {update_error}")
                    conn.rollback()
            
        else:
            print(f"❌ Erro de integridade: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_and_add_super_admin()