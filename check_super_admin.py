#!/usr/bin/env python3
"""
Script para verificar e gerenciar credenciais do Super Admin
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import uuid
from werkzeug.security import generate_password_hash
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

def check_super_admin():
    """Verificar e gerenciar Super Admin"""
    
    # Configuração do banco
    database_url = os.getenv('POSTGRESQL_URL')
    if not database_url:
        print("❌ POSTGRESQL_URL não encontrada no .env")
        return False
    
    print(f"🔗 Conectando ao banco de dados...")
    
    try:
        # Criar conexão
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("✅ Conexão estabelecida com sucesso!")
            
            # 1. Verificar se existem usuários Super Admin
            result = conn.execute(text("""
                SELECT id, name, email, cpf, is_active, created_at, password_hash
                FROM users 
                WHERE user_type = 'super_admin'
                ORDER BY created_at DESC;
            """))
            
            super_admins = result.fetchall()
            
            if super_admins:
                print(f"\n👑 Super Admins encontrados ({len(super_admins)}):")
                print("=" * 60)
                
                for i, admin in enumerate(super_admins, 1):
                    print(f"\n{i}. Super Admin:")
                    print(f"   📧 Email: {admin[2]}")
                    print(f"   👤 Nome: {admin[1]}")
                    print(f"   🆔 CPF: {admin[3]}")
                    print(f"   ✅ Status: {'Ativo' if admin[4] else 'Inativo'}")
                    print(f"   📅 Criado: {admin[5]}")
                    print(f"   🔐 Senha definida: {'Sim' if admin[6] and admin[6] != '$2b$12$dummy_hash_for_super_admin' else 'Não (senha temporária)'}")
                
                # Mostrar credenciais padrão se existir
                default_admin = None
                for admin in super_admins:
                    if admin[2] == 'superadmin@federal.com' or 'super_' in admin[2]:
                        default_admin = admin
                        break
                
                if default_admin:
                    print(f"\n🎯 CREDENCIAIS DE LOGIN:")
                    print("=" * 40)
                    print(f"📧 Email: {default_admin[2]}")
                    print(f"🔑 Senha: admin123 (padrão)")
                    print("=" * 40)
                else:
                    print(f"\n🎯 CREDENCIAIS DE LOGIN:")
                    print("=" * 40)
                    print(f"📧 Email: {super_admins[0][2]}")
                    print(f"🔑 Senha: admin123 (padrão)")
                    print("=" * 40)
                
                return True
            
            else:
                print("\n⚠️  Nenhum Super Admin encontrado!")
                print("🔧 Criando Super Admin padrão...")
                
                # Criar Super Admin padrão
                super_admin_id = str(uuid.uuid4())
                email = "superadmin@federal.com"
                password_hash = generate_password_hash("admin123")
                
                conn.execute(text("""
                    INSERT INTO users (
                        id, cpf, email, password_hash, user_type, name, 
                        created_at, updated_at, is_active, first_access_completed
                    ) VALUES (
                        :id, :cpf, :email, :password_hash, :user_type, :name,
                        :created_at, :updated_at, :is_active, :first_access_completed
                    )
                """), {
                    'id': super_admin_id,
                    'cpf': '00000000001',
                    'email': email,
                    'password_hash': password_hash,
                    'user_type': 'super_admin',
                    'name': 'Super Administrador',
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'is_active': True,
                    'first_access_completed': True
                })
                
                conn.commit()
                
                print("✅ Super Admin criado com sucesso!")
                print(f"\n🎯 CREDENCIAIS DE LOGIN:")
                print("=" * 40)
                print(f"📧 Email: {email}")
                print(f"🔑 Senha: admin123")
                print("=" * 40)
                
                return True
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print("👑 Verificando credenciais do Super Admin...")
    print("=" * 60)
    
    success = check_super_admin()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Verificação concluída!")
    else:
        print("❌ Verificação falhou!")
        sys.exit(1)