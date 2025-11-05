#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.user import User
from config.database import db
from app import create_app

def get_client_info():
    app = create_app()
    with app.app_context():
        # Buscar o usuário cliente existente
        cliente = User.query.filter_by(user_type='cliente').first()
        
        if cliente:
            print("=== CREDENCIAIS DE LOGIN CLIENTE ===")
            print(f"Nome: {cliente.name}")
            print(f"Email: {cliente.email}")
            print(f"CPF: {cliente.cpf}")
            print(f"Tipo: {cliente.user_type}")
            print(f"Ativo: {'Sim' if cliente.is_active else 'Não'}")
            print(f"Criado em: {cliente.created_at}")
            print("\n=== PARA FAZER LOGIN ===")
            print(f"Email: {cliente.email}")
            print("Senha: [Você precisa saber a senha que foi definida]")
            print("\nOBS: Se não souber a senha, posso criar um novo usuário cliente com credenciais conhecidas.")
        else:
            print("Nenhum usuário cliente encontrado.")

if __name__ == "__main__":
    get_client_info()