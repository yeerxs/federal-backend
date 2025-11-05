#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.user import User
from config.database import db
from app import create_app

def check_users():
    app = create_app()
    with app.app_context():
        # Verificar usuários existentes
        users = User.query.all()
        print(f'Total de usuários: {len(users)}')
        
        clientes = User.query.filter_by(user_type='cliente').all()
        print(f'Usuários clientes: {len(clientes)}')
        
        if clientes:
            print('\nUsuários clientes existentes:')
            for cliente in clientes:
                print(f'- Nome: {cliente.name}, Email: {cliente.email}, CPF: {cliente.cpf}')
        else:
            print('\nNenhum usuário cliente encontrado.')
        
        # Verificar todos os tipos de usuário
        print('\nTodos os usuários por tipo:')
        for user in users:
            print(f'- {user.name} ({user.email}) - Tipo: {user.user_type}')
        
        return len(clientes)

if __name__ == "__main__":
    check_users()