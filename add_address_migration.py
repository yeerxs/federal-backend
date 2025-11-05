#!/usr/bin/env python3

import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

from src.app import create_app
from src.config.database import db

def add_address_column():
    """Adiciona o campo address à tabela users"""
    app = create_app()
    
    with app.app_context():
        try:
            # Executar a migração
            db.engine.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS address VARCHAR(500);')
            print('✅ Campo address adicionado com sucesso à tabela users!')
        except Exception as e:
            print(f'❌ Erro ao adicionar campo address: {str(e)}')
            # Se o erro for que a coluna já existe, não é um problema
            if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                print('✅ Campo address já existe na tabela users!')
            else:
                raise e

if __name__ == '__main__':
    add_address_column()