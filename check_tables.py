#!/usr/bin/env python3
"""
Script para verificar as tabelas do banco de dados
"""

import sqlite3
import os

def check_tables():
    db_path = 'instance/federal_associados.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("📋 Tabelas existentes:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verificar especificamente as tabelas de permissões
        permission_tables = ['permissions', 'user_permissions']
        for table in permission_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            exists = cursor.fetchone()
            if exists:
                print(f"✅ Tabela {table} existe")
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   📊 {count} registros")
            else:
                print(f"❌ Tabela {table} NÃO existe")
        
        # Verificar usuários
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"👥 {user_count} usuários no banco")
            
            # Verificar tipos de usuários
            cursor.execute("SELECT user_type, COUNT(*) FROM users GROUP BY user_type")
            user_types = cursor.fetchall()
            print("📊 Tipos de usuários:")
            for user_type, count in user_types:
                print(f"  - {user_type}: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return False

if __name__ == "__main__":
    check_tables()