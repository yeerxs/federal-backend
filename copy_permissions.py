#!/usr/bin/env python3
"""
Script para copiar tabelas de permissões do banco federal_system.db para federal_associados.db
"""

import sqlite3
import os

def copy_permissions_tables():
    """Copia as tabelas de permissões entre os bancos"""
    
    source_db = 'instance/federal_system.db'
    target_db = 'instance/federal_associados.db'
    
    if not os.path.exists(source_db):
        print(f"❌ Banco de origem não encontrado: {source_db}")
        return False
        
    if not os.path.exists(target_db):
        print(f"❌ Banco de destino não encontrado: {target_db}")
        return False
    
    try:
        # Conectar aos bancos
        source_conn = sqlite3.connect(source_db)
        target_conn = sqlite3.connect(target_db)
        
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Verificar tabelas no banco de origem
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('permissions', 'user_permissions')")
        tables = [row[0] for row in source_cursor.fetchall()]
        print(f"Tabelas encontradas no banco de origem: {tables}")
        
        # Copiar tabela permissions
        if 'permissions' in tables:
            # Obter estrutura
            source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='permissions'")
            create_sql = source_cursor.fetchone()[0]
            
            # Recriar tabela no destino
            target_cursor.execute("DROP TABLE IF EXISTS permissions")
            target_cursor.execute(create_sql)
            
            # Copiar dados
            source_cursor.execute("SELECT * FROM permissions")
            data = source_cursor.fetchall()
            
            if data:
                # Obter número de colunas
                source_cursor.execute("PRAGMA table_info(permissions)")
                columns = len(source_cursor.fetchall())
                placeholders = ','.join(['?' for _ in range(columns)])
                
                target_cursor.executemany(f"INSERT INTO permissions VALUES ({placeholders})", data)
                print(f"✅ Tabela permissions copiada com {len(data)} registros")
            else:
                print("⚠️ Tabela permissions está vazia")
        
        # Copiar tabela user_permissions
        if 'user_permissions' in tables:
            # Obter estrutura
            source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user_permissions'")
            create_sql = source_cursor.fetchone()[0]
            
            # Recriar tabela no destino
            target_cursor.execute("DROP TABLE IF EXISTS user_permissions")
            target_cursor.execute(create_sql)
            
            # Copiar dados
            source_cursor.execute("SELECT * FROM user_permissions")
            data = source_cursor.fetchall()
            
            if data:
                # Obter número de colunas
                source_cursor.execute("PRAGMA table_info(user_permissions)")
                columns = len(source_cursor.fetchall())
                placeholders = ','.join(['?' for _ in range(columns)])
                
                target_cursor.executemany(f"INSERT INTO user_permissions VALUES ({placeholders})", data)
                print(f"✅ Tabela user_permissions copiada com {len(data)} registros")
            else:
                print("⚠️ Tabela user_permissions está vazia")
        
        # Confirmar mudanças
        target_conn.commit()
        
        # Verificar se as tabelas foram criadas no destino
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('permissions', 'user_permissions')")
        target_tables = [row[0] for row in target_cursor.fetchall()]
        print(f"Tabelas criadas no banco de destino: {target_tables}")
        
        # Fechar conexões
        source_conn.close()
        target_conn.close()
        
        print("✅ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False

if __name__ == "__main__":
    copy_permissions_tables()