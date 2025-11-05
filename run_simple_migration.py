#!/usr/bin/env python3
"""
Script para executar a migração do sistema simplificado de contratos
"""

import sqlite3
import os
import sys

def run_migration():
    """Executa a migração para o sistema simplificado"""
    
    # Caminho para o banco de dados
    db_path = os.path.join(os.path.dirname(__file__), 'federal_system.db')
    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', 'create_simple_contract_system.sql')
    
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ler o arquivo de migração
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Executar a migração
        print("Executando migração para sistema simplificado...")
        cursor.executescript(migration_sql)
        
        # Confirmar as mudanças
        conn.commit()
        
        print("✅ Migração executada com sucesso!")
        print("Sistema simplificado de contratos criado.")
        
        # Verificar se as tabelas foram criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("\n📋 Tabelas criadas:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verificar dados iniciais
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        admin_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contracts")
        contract_count = cursor.fetchone()[0]
        
        print(f"\n📊 Dados iniciais:")
        print(f"  - Administradores: {admin_count}")
        print(f"  - Contratos: {contract_count}")
        
    except sqlite3.Error as e:
        print(f"❌ Erro na migração: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ Arquivo não encontrado: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()