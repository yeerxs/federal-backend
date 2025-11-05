#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app
from models.user import db, User
from werkzeug.security import generate_password_hash

def create_test_users():
    app = create_app()
    
    with app.app_context():
        # Criar admin
        admin = User.query.filter_by(email='admin@federal.com').first()
        if not admin:
            admin = User(
                cpf='12345678901',
                email='admin@federal.com',
                password_hash=generate_password_hash('admin123'),
                name='Administrador Federal',
                user_type='admin',
                phone='11999999999',
                address='Endereço do Admin'
            )
            db.session.add(admin)
            print('Admin criado com sucesso!')
            print('Email: admin@federal.com')
            print('Senha: admin123')
        else:
            print('Admin já existe!')
            print('Email: admin@federal.com')
            print('Senha: admin123')

        # Criar cliente
        client = User.query.filter_by(email='cliente@teste.com').first()
        if not client:
            client = User(
                cpf='98765432101',
                email='cliente@teste.com',
                password_hash=generate_password_hash('cliente123'),
                name='Cliente Teste',
                user_type='cliente',
                phone='11988888888',
                address='Endereço do Cliente'
            )
            db.session.add(client)
            print('\nCliente criado com sucesso!')
            print('Email: cliente@teste.com')
            print('Senha: cliente123')
        else:
            print('\nCliente já existe!')
            print('Email: cliente@teste.com')
            print('Senha: cliente123')

        db.session.commit()

if __name__ == '__main__':
    create_test_users()
