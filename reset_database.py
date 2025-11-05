#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para resetar completamente o banco de dados e aplicar o sistema simplificado
"""

import sqlite3
import os
import shutil
from datetime import datetime

def reset_database():
    """Reset completo do banco de dados"""
    db_path = 'federal_system.db'
    
    try:
        # Fazer backup do banco atual se existir
        if os.path.exists(db_path):
            backup_name = f'federal_system_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(db_path, backup_name)
            print(f"✅ Backup criado: {backup_name}")
            
            # Remover banco atual
            os.remove(db_path)
            print("✅ Banco de dados antigo removido")
        
        # Conectar ao novo banco (será criado automaticamente)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ler e executar o script de migração
        with open('migrations/create_simple_contract_system.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Executar todas as instruções SQL
        cursor.executescript(migration_sql)
        
        # Confirmar as mudanças
        conn.commit()
        
        print("✅ Migração executada com sucesso!")
        
        # Verificar se as tabelas foram criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Tabelas criadas: {[table[0] for table in tables]}")
        
        # Verificar dados iniciais
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Usuários criados: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM contracts")
        contract_count = cursor.fetchone()[0]
        print(f"✅ Contratos criados: {contract_count}")
        
        conn.close()
        print("✅ Reset do banco de dados concluído com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro SQLite: {e}")
        return False
    except FileNotFoundError as e:
        print(f"❌ Arquivo não encontrado: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Resetando banco de dados para sistema simplificado...")
    success = reset_database()
    if success:
        print("\n🎉 Sistema simplificado pronto para uso!")
    else:
        print("\n❌ Falha no reset do banco de dados")