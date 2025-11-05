#!/usr/bin/env python3
"""
Script para executar migração do Sistema de Assinatura Digital
Federal Associados - Segurança Máxima
"""

import sqlite3
import os

def execute_migration():
    # Conectar ao banco de dados
    db_path = os.path.join('src', 'instance', 'federal_associados.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ler o arquivo de migração
    migration_file = 'migrations/create_digital_signature_tables_v2.sql'
    
    if not os.path.exists(migration_file):
        print(f"❌ Arquivo de migração não encontrado: {migration_file}")
        return False

    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()

    print("🚀 Iniciando migração do Sistema de Assinatura Digital...")
    
    try:
        # Executar todo o script SQL de uma vez
        cursor.executescript(migration_sql)
        conn.commit()
        print("✅ Migração executada com sucesso!")
        
        # Verificar se as tabelas foram criadas
        signature_tables = [
            'encryption_keys', 'biometric_profiles', 'digital_certificates', 
            'signature_documents', 'digital_signatures', 'signature_timestamps',
            'biometric_validations', 'signature_audit_logs'
        ]

        print('\n🔍 Verificando tabelas criadas:')
        created_count = 0
        for table_name in signature_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            result = cursor.fetchone()
            if result:
                print(f'  ✅ {table_name}')
                created_count += 1
            else:
                print(f'  ❌ {table_name}')

        print(f'\n📊 Resultado: {created_count}/{len(signature_tables)} tabelas criadas')
        
        if created_count == len(signature_tables):
            print("🎉 Todas as tabelas do Sistema de Assinatura Digital foram criadas com sucesso!")
            return True
        else:
            print("⚠️ Algumas tabelas não foram criadas. Verifique os logs acima.")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = execute_migration()
    if success:
        print("\n✅ Migração concluída com sucesso!")
    else:
        print("\n❌ Migração falhou!")