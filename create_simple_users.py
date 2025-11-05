#!/usr/bin/env python3
"""
Script para criar usuários de teste simples
Sistema Federal Associados - Login Simples
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from werkzeug.security import generate_password_hash
from config.database import db
from models.user import User
from src.app import create_app
import uuid

def create_simple_users():
    """Criar usuários de teste simples"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se usuários já existem
            admin_exists = User.query.filter_by(email='admin@federal.com').first()
            client_exists = User.query.filter_by(email='cliente@federal.com').first()
            
            if admin_exists:
                print("✅ Usuário admin já existe")
            else:
                # Criar usuário admin
                admin_user = User(
                    id=uuid.uuid4(),
                    name="Administrador Sistema",
                    email="admin@federal.com",
                    cpf="11144477735",  # CPF de teste
                    password_hash=generate_password_hash("admin123"),
                    user_type="admin",
                    phone="11999999999",
                    address="Endereço Admin",
                    is_active=True
                )
                db.session.add(admin_user)
                print("✅ Usuário admin criado: admin@federal.com / admin123")
            
            if client_exists:
                print("✅ Usuário cliente já existe")
            else:
                # Criar usuário cliente
                client_user = User(
                    id=uuid.uuid4(),
                    name="Cliente Teste",
                    email="cliente@federal.com",
                    cpf="22255588899",  # CPF de teste
                    password_hash=generate_password_hash("cliente123"),
                    user_type="cliente",
                    phone="11888888888",
                    address="Endereço Cliente",
                    is_active=True
                )
                db.session.add(client_user)
                print("✅ Usuário cliente criado: cliente@federal.com / cliente123")
            
            # Salvar no banco
            db.session.commit()
            print("\n🎉 Usuários de teste criados com sucesso!")
            print("\n📋 Credenciais de Login:")
            print("👤 Admin: admin@federal.com / admin123")
            print("👤 Cliente: cliente@federal.com / cliente123")
            
        except Exception as e:
            print(f"❌ Erro ao criar usuários: {e}")
            db.session.rollback()

if __name__ == "__main__":
    create_simple_users()