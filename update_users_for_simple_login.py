#!/usr/bin/env python3
"""
Script para atualizar usuários existentes para login simples
Sistema Federal Associados - Login Simples
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from werkzeug.security import generate_password_hash
from config.database import db
from models.user import User
from src.app import create_app

def update_users_for_simple_login():
    """Atualizar usuários existentes para login simples"""
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar usuários existentes
            admin_user = User.query.filter_by(email='admin@federalassociados.com').first()
            if admin_user:
                # Atualizar email e senha do admin
                admin_user.email = 'admin@federal.com'
                admin_user.password_hash = generate_password_hash('admin123')
                print("✅ Admin atualizado: admin@federal.com / admin123")
            
            # Buscar cliente existente
            client_user = User.query.filter_by(email='isaac@example.com').first()
            if client_user:
                # Atualizar email e senha do cliente
                client_user.email = 'cliente@federal.com'
                client_user.password_hash = generate_password_hash('cliente123')
                print("✅ Cliente atualizado: cliente@federal.com / cliente123")
            
            # Verificar se não existem, criar novos
            if not admin_user:
                # Buscar por admin@teste.com
                admin_test = User.query.filter_by(email='admin@teste.com').first()
                if admin_test:
                    admin_test.email = 'admin@federal.com'
                    admin_test.password_hash = generate_password_hash('admin123')
                    print("✅ Admin teste atualizado: admin@federal.com / admin123")
            
            if not client_user:
                # Buscar por cliente@teste.com
                client_test = User.query.filter_by(email='cliente@teste.com').first()
                if client_test:
                    client_test.email = 'cliente@federal.com'
                    client_test.password_hash = generate_password_hash('cliente123')
                    print("✅ Cliente teste atualizado: cliente@federal.com / cliente123")
            
            # Salvar no banco
            db.session.commit()
            print("\n🎉 Usuários atualizados com sucesso!")
            print("\n📋 Credenciais de Login:")
            print("👤 Admin: admin@federal.com / admin123")
            print("👤 Cliente: cliente@federal.com / cliente123")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar usuários: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_users_for_simple_login()