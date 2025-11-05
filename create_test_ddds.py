#!/usr/bin/env python3
"""
Script para criar DDDs de teste no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.user import db, DDD, User
from src.app import create_app
import uuid

def create_test_ddds():
    app = create_app()
    
    with app.app_context():
        # Buscar um usuário admin para ser o criador
        admin_user = User.query.filter_by(user_type='admin').first()
        if not admin_user:
            print("❌ Nenhum usuário admin encontrado")
            return
        
        print(f"✅ Usando admin: {admin_user.name}")
        
        # DDDs de teste para cada operadora
        test_ddds = [
            # Vivo
            {'operator': 'vivo', 'ddd': '11'},
            {'operator': 'vivo', 'ddd': '21'},
            {'operator': 'vivo', 'ddd': '31'},
            {'operator': 'vivo', 'ddd': '41'},
            {'operator': 'vivo', 'ddd': '51'},
            
            # Claro
            {'operator': 'claro', 'ddd': '11'},
            {'operator': 'claro', 'ddd': '21'},
            {'operator': 'claro', 'ddd': '31'},
            {'operator': 'claro', 'ddd': '41'},
            {'operator': 'claro', 'ddd': '51'},
            
            # TIM
            {'operator': 'tim', 'ddd': '11'},
            {'operator': 'tim', 'ddd': '21'},
            {'operator': 'tim', 'ddd': '31'},
            {'operator': 'tim', 'ddd': '41'},
            {'operator': 'tim', 'ddd': '51'},
        ]
        
        created_count = 0
        
        for ddd_data in test_ddds:
            # Verificar se já existe
            existing = DDD.query.filter_by(
                operator=ddd_data['operator'],
                ddd=ddd_data['ddd']
            ).first()
            
            if existing:
                print(f"⚠️  DDD {ddd_data['ddd']} para {ddd_data['operator']} já existe")
                continue
            
            # Criar novo DDD
            new_ddd = DDD(
                operator=ddd_data['operator'],
                ddd=ddd_data['ddd'],
                is_active=True,
                created_by=admin_user.id
            )
            
            db.session.add(new_ddd)
            created_count += 1
            print(f"✅ Criado DDD {ddd_data['ddd']} para {ddd_data['operator']}")
        
        try:
            db.session.commit()
            print(f"\n🎉 {created_count} DDDs criados com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar DDDs: {e}")

if __name__ == "__main__":
    create_test_ddds()