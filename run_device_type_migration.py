#!/usr/bin/env python3
"""
Script para executar migração do device_type
Federal Associados - Correção de Banco
"""

import sqlite3
import os

def run_migration():
    # Conectar ao banco de dados
    db_path = os.path.join('src', 'instance', 'federal_associados.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verificar se a coluna device_type já existe
        cursor.execute("PRAGMA table_info(activations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'device_type' in columns:
            print("✅ Coluna device_type já existe na tabela activations")
        else:
            print("📝 Adicionando coluna device_type à tabela activations...")
            
            # Adicionar coluna device_type (SQLite não suporta ENUM, usaremos TEXT)
            cursor.execute("ALTER TABLE activations ADD COLUMN device_type TEXT")
            
            print("✅ Coluna device_type adicionada com sucesso!")
        
        conn.commit()
        
        # Verificar estrutura final
        cursor.execute("PRAGMA table_info(activations)")
        columns = cursor.fetchall()
        print("\n📋 Estrutura atual da tabela activations:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")

    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()