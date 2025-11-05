#!/usr/bin/env python3
"""
Script para executar migração do Sistema de Assinatura Digital
Federal Associados - Segurança Máxima
"""

import sqlite3
import os

def run_migration():
    # Conectar ao banco de dados
    db_path = os.path.join('src', 'instance', 'federal_associados.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ler e executar o arquivo de migração
    with open('migrations/create_digital_signature_tables_v2.sql', 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    # Executar cada comando SQL separadamente
    commands = migration_sql.split(';')
    for command in commands:
        command = command.strip()
        if command and not command.startswith('--'):
            try:
                cursor.execute(command)
                print(f'✓ Executado: {command[:50]}...')
            except Exception as e:
                print(f'✗ Erro: {e}')

    conn.commit()

    # Verificar se as tabelas foram criadas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%signature%' OR name LIKE '%biometric%' OR name LIKE '%certificate%' OR name LIKE '%encryption%')")
    tables = cursor.fetchall()
    print('\n📋 Tabelas criadas:')
    for table in tables:
        print(f'  - {table[0]}')

    conn.close()
    print('\n🎉 Migração de assinatura digital concluída!')

if __name__ == '__main__':
    run_migration()