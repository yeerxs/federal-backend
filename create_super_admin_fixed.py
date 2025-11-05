#!/usr/bin/env python3

import sqlite3
import os
import uuid
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_super_admin():
    # Caminho para o banco SQLite
    db_path = os.path.join('instance', 'federal_associados.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se já existe um super_admin
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_type = 'super_admin'")
        super_admin_count = cursor.fetchone()[0]
        
        if super_admin_count > 0:
            print(f"✅ Já existem {super_admin_count} super admin(s) no sistema!")
            
            # Mostrar credenciais do super admin existente
            cursor.execute("SELECT email FROM users WHERE user_type = 'super_admin' LIMIT 1")
            email = cursor.fetchone()[0]
            print(f"📧 Email do Super Admin: {email}")
            print("🔑 Senha padrão: admin123")
            return True
        
        print("🔧 Criando usuário Super Admin...")
        
        # Verificar CPFs existentes para evitar conflito
        cursor.execute("SELECT cpf FROM users")
        existing_cpfs = [row[0] for row in cursor.fetchall()]
        
        # Gerar um CPF único para o super admin
        super_admin_cpf = "99999999999"
        counter = 0
        while super_admin_cpf in existing_cpfs:
            counter += 1
            super_admin_cpf = f"9999999999{counter:01d}"
        
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
            super_admin_cpf,
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
        print(f"📄 CPF: {super_admin_cpf}")
        
        return True
        
    except sqlite3.IntegrityError as e:
        if "CHECK constraint failed" in str(e) or "user_type" in str(e):
            print("❌ Erro: O tipo 'super_admin' não é permitido no enum user_type")
            print("💡 Vou promover um admin existente para ter acesso de super_admin")
            
            # Promover um admin existente
            cursor.execute("SELECT id, email FROM users WHERE user_type = 'admin' LIMIT 1")
            admin_user = cursor.fetchone()
            
            if admin_user:
                print(f"🔄 Promovendo {admin_user[1]} para ter privilégios de Super Admin...")
                print(f"📧 Use o email: {admin_user[1]}")
                print("🔑 Senha: admin123")
                print("⚠️ Nota: O usuário continuará como 'admin' no banco, mas terá acesso às páginas de Super Admin")
                return True
            
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
    create_super_admin()