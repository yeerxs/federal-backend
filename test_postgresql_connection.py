#!/usr/bin/env python3
"""
Script para testar a conexão PostgreSQL e verificar as tabelas
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

def test_connection():
    """Testa a conexão e faz consultas básicas"""
    try:
        connection_params = {
            'host': os.getenv('SUPABASE_DB_HOST'),
            'port': os.getenv('SUPABASE_DB_PORT', 5432),
            'database': os.getenv('SUPABASE_DB_NAME'),
            'user': os.getenv('SUPABASE_DB_USER'),
            'password': os.getenv('SUPABASE_DB_PASSWORD'),
            'sslmode': 'require'
        }
        
        print("=== Teste de Conexão PostgreSQL ===")
        print(f"Host: {connection_params['host']}")
        print(f"Database: {connection_params['database']}")
        print()
        
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # Testar consulta básica na tabela users
        print("1. Testando consulta na tabela users...")
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"✓ Total de usuários: {user_count}")
        
        # Verificar se o admin existe
        print("\n2. Verificando usuário admin...")
        cursor.execute("SELECT email, name, user_type FROM users WHERE email = 'admin@federal.com';")
        admin = cursor.fetchone()
        if admin:
            print(f"✓ Admin encontrado: {admin[1]} ({admin[0]}) - Tipo: {admin[2]}")
        else:
            print("✗ Admin não encontrado")
        
        # Listar todas as tabelas
        print("\n3. Listando tabelas criadas...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"✓ Tabela: {table[0]}")
        
        # Testar consulta na tabela tokens
        print("\n4. Testando tabela tokens...")
        cursor.execute("SELECT COUNT(*) FROM tokens;")
        token_count = cursor.fetchone()[0]
        print(f"✓ Total de tokens: {token_count}")
        
        print("\n✅ Todos os testes passaram! PostgreSQL está funcionando corretamente.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)