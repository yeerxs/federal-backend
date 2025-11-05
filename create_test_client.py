#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.user import User
from config.database import db
from app import create_app
from werkzeug.security import generate_password_hash

def create_test_client():
    app = create_app()
    with app.app_context():
        # Verificar se já existe um cliente de teste
        existing_client = User.query.filter_by(email='cliente@teste.com').first()
        
        if existing_client:
            print("=== CLIENTE DE TESTE JÁ EXISTE ===")
            print(f"Nome: {existing_client.name}")
            print(f"Email: {existing_client.email}")
            print(f"CPF: {existing_client.cpf}")
            print(f"Tipo: {existing_client.user_type}")
            print("\n=== CREDENCIAIS PARA LOGIN ===")
            print("Email: cliente@teste.com")
            print("Senha: cliente123")
            return
        
        # Criar novo cliente de teste
        try:
            new_client = User(
                cpf='98765432100',
                email='cliente@teste.com',
                password_hash=generate_password_hash('cliente123'),
                user_type='cliente',
                name='Cliente Teste',
                phone='11999999999',
                is_active=True
            )
            
            db.session.add(new_client)
            db.session.commit()
            
            print("=== CLIENTE DE TESTE CRIADO COM SUCESSO ===")
            print(f"Nome: {new_client.name}")
            print(f"Email: {new_client.email}")
            print(f"CPF: {new_client.cpf}")
            print(f"Tipo: {new_client.user_type}")
            print("\n=== CREDENCIAIS PARA LOGIN ===")
            print("Email: cliente@teste.com")
            print("Senha: cliente123")
            
        except Exception as e:
            print(f"Erro ao criar cliente de teste: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_test_client()