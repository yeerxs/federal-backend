#!/usr/bin/env python3
"""
Script para executar a migração do sistema de login e primeiro acesso
Federal Associados - Sistema Unificado de Autenticação
"""

import sqlite3
import os
from datetime import datetime

def run_login_migration():
    """Executa a migração para o sistema de login e primeiro acesso"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('federal_system.db')
    if not os.path.exists(db_path):
        db_path = os.path.join('instance', 'federal_system.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Iniciando migração do sistema de login e primeiro acesso...")
    
    try:
        # Ler o arquivo de migração
        migration_file = os.path.join('migrations', 'create_login_primeiro_acesso_system.sql')
        
        if not os.path.exists(migration_file):
            print(f"❌ Arquivo de migração não encontrado: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Dividir o SQL em comandos individuais
        commands = [cmd.strip() for cmd in migration_sql.split(';') if cmd.strip()]
        
        # Executar cada comando
        for i, command in enumerate(commands, 1):
            if command.strip():
                try:
                    cursor.execute(command)
                    print(f"✅ Comando {i}/{len(commands)} executado com sucesso")
                except Exception as e:
                    print(f"⚠️ Aviso no comando {i}: {e}")
                    # Continuar mesmo com avisos (como tabelas que já existem)
        
        # Commit das mudanças
        conn.commit()
        
        # Verificar se as tabelas foram criadas
        tables_to_check = [
            'verification_codes',
            'contract_validations', 
            'temporary_sessions',
            'system_config'
        ]
        
        print("\n📋 Verificando tabelas criadas:")
        for table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            result = cursor.fetchone()
            if result:
                print(f"✅ Tabela '{table}' criada com sucesso")
            else:
                print(f"❌ Tabela '{table}' não foi criada")
        
        # Verificar configurações do sistema
        cursor.execute("SELECT COUNT(*) FROM system_config")
        config_count = cursor.fetchone()[0]
        print(f"✅ {config_count} configurações do sistema inseridas")
        
        # Verificar status do admin
        cursor.execute("SELECT status, first_access_completed FROM users WHERE cpf = '12345678990'")
        admin_result = cursor.fetchone()
        if admin_result:
            print(f"✅ Admin atualizado - Status: {admin_result[0]}, Primeiro acesso: {admin_result[1]}")
        
        print("\n🎉 Migração do sistema de login e primeiro acesso concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def verify_migration():
    """Verifica se a migração foi aplicada corretamente"""
    
    db_path = os.path.join('federal_system.db')
    if not os.path.exists(db_path):
        db_path = os.path.join('instance', 'federal_system.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verificando estrutura das novas tabelas:")
    
    tables = {
        'verification_codes': ['id', 'user_id', 'identifier', 'code', 'email', 'expires_at', 'used', 'created_at'],
        'contract_validations': ['id', 'user_id', 'identifier', 'approved', 'partner_response', 'validated_at'],
        'temporary_sessions': ['id', 'identifier', 'session_token', 'session_type', 'expires_at', 'used'],
        'system_config': ['id', 'key', 'value', 'description', 'created_at', 'updated_at']
    }
    
    for table_name, expected_columns in tables.items():
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"\n📋 Tabela '{table_name}':")
            for col in expected_columns:
                if col in column_names:
                    print(f"  ✅ {col}")
                else:
                    print(f"  ❌ {col} (não encontrada)")
        
        except Exception as e:
            print(f"❌ Erro ao verificar tabela {table_name}: {e}")
    
    conn.close()

if __name__ == "__main__":
    success = run_login_migration()
    if success:
        verify_migration()
    else:
        print("❌ Migração falhou!")