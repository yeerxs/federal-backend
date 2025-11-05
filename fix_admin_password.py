#!/usr/bin/env python3
"""
Script para corrigir a senha do admin no PostgreSQL
"""

import os
import sys
import psycopg2
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

def fix_admin_password():
    """Corrige a senha do admin no PostgreSQL"""
    try:
        connection_params = {
            'host': os.getenv('SUPABASE_DB_HOST'),
            'port': os.getenv('SUPABASE_DB_PORT', 5432),
            'database': os.getenv('SUPABASE_DB_NAME'),
            'user': os.getenv('SUPABASE_DB_USER'),
            'password': os.getenv('SUPABASE_DB_PASSWORD'),
            'sslmode': 'require'
        }
        
        print("=== Correção da Senha do Admin ===")
        
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # Gerar hash correto para a senha 'admin123'
        correct_password_hash = generate_password_hash('admin123')
        print(f"Hash gerado: {correct_password_hash}")
        
        # Atualizar a senha do admin
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s 
            WHERE email = 'admin@federal.com'
        """, (correct_password_hash,))
        
        # Verificar se foi atualizado
        cursor.execute("SELECT email, name FROM users WHERE email = 'admin@federal.com'")
        admin = cursor.fetchone()
        
        if admin:
            print(f"✓ Senha do admin atualizada: {admin[1]} ({admin[0]})")
            conn.commit()
        else:
            print("✗ Admin não encontrado")
            
        cursor.close()
        conn.close()
        
        print("✅ Senha do admin corrigida com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir senha: {e}")
        return False

if __name__ == "__main__":
    success = fix_admin_password()
    sys.exit(0 if success else 1)