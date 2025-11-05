#!/usr/bin/env python3
"""
Script para testar autenticação e verificar se o usuário está logado corretamente
"""

import sqlite3
import os
import sys

# Adicionar o diretório src ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.user import User
from config.database import db
from app import create_app

def test_users_and_auth():
    """Testar usuários e verificar dados de autenticação"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 TESTE DE AUTENTICAÇÃO E USUÁRIOS")
        print("=" * 50)
        
        # Verificar usuários no banco
        users = User.query.all()
        print(f"\n📊 Total de usuários no banco: {len(users)}")
        
        for user in users:
            print(f"\n👤 Usuário: {user.name}")
            print(f"   📧 Email: {user.email}")
            print(f"   🆔 CPF: {user.cpf}")
            print(f"   🏷️ Tipo: {user.user_type}")
            print(f"   ✅ Ativo: {user.is_active}")
            print(f"   🔑 ID: {user.id}")
            
        # Verificar especificamente super_admin
        super_admin = User.query.filter_by(user_type='super_admin').first()
        if super_admin:
            print(f"\n🔐 SUPER ADMIN ENCONTRADO:")
            print(f"   👤 Nome: {super_admin.name}")
            print(f"   📧 Email: {super_admin.email}")
            print(f"   🆔 CPF: {super_admin.cpf}")
            print(f"   ✅ Ativo: {super_admin.is_active}")
            print(f"   🔑 ID: {super_admin.id}")
        else:
            print("\n❌ NENHUM SUPER ADMIN ENCONTRADO!")
            
        # Verificar admins
        admins = User.query.filter_by(user_type='admin').all()
        print(f"\n👥 ADMINS ENCONTRADOS: {len(admins)}")
        for admin in admins:
            print(f"   👤 {admin.name} - {admin.email} (Ativo: {admin.is_active})")

if __name__ == "__main__":
    test_users_and_auth()