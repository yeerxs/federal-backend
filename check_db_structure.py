#!/usr/bin/env python3
"""
Script para verificar a estrutura atual do banco de dados
"""

import sqlite3
import os

def check_database_structure():
    """Verifica a estrutura atual do banco de dados"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'federal_system.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📋 Tabelas existentes:")
        for table in tables:
            table_name = table[0]
            print(f"\n🔹 {table_name}")
            
            # Mostrar estrutura da tabela
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''} {'NOT NULL' if col[3] else ''}")
        
        # Verificar se existe tabela contracts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contracts'")
        contracts_exists = cursor.fetchone()
        
        if contracts_exists:
            print("\n📊 Dados na tabela contracts:")
            cursor.execute("SELECT COUNT(*) FROM contracts")
            count = cursor.fetchone()[0]
            print(f"  - Total de registros: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, title, status FROM contracts LIMIT 5")
                contracts = cursor.fetchall()
                for contract in contracts:
                    print(f"  - ID: {contract[0]}, Título: {contract[1][:50]}..., Status: {contract[2]}")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao verificar banco: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database_structure()