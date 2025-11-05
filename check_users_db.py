#!/usr/bin/env python3
"""
Script para verificar inconsistências no banco de dados de usuários
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def check_database():
    """Verificar estado do banco de dados"""
    
    # Configuração do banco
    database_url = os.getenv('POSTGRESQL_URL')
    if not database_url:
        print("❌ POSTGRESQL_URL não encontrada no .env")
        return False
    
    print(f"🔗 Conectando ao banco: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    
    try:
        # Criar conexão
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("✅ Conexão estabelecida com sucesso!")
            
            # 1. Verificar se a tabela users existe
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                print("❌ Tabela 'users' não existe!")
                return False
            
            print("✅ Tabela 'users' existe")
            
            # 2. Contar total de usuários
            result = conn.execute(text("SELECT COUNT(*) FROM users;"))
            total_users = result.fetchone()[0]
            print(f"📊 Total de usuários no banco: {total_users}")
            
            # 3. Verificar usuários por tipo
            result = conn.execute(text("""
                SELECT user_type, COUNT(*) 
                FROM users 
                GROUP BY user_type 
                ORDER BY user_type;
            """))
            
            print("\n📋 Usuários por tipo:")
            for row in result:
                print(f"  - {row[0]}: {row[1]} usuários")
            
            # 4. Verificar usuários ativos/inativos
            result = conn.execute(text("""
                SELECT is_active, COUNT(*) 
                FROM users 
                GROUP BY is_active 
                ORDER BY is_active;
            """))
            
            print("\n🔄 Status dos usuários:")
            for row in result:
                status = "Ativo" if row[0] else "Inativo"
                print(f"  - {status}: {row[1]} usuários")
            
            # 5. Listar alguns usuários para verificação
            result = conn.execute(text("""
                SELECT id, name, email, cpf, user_type, is_active, created_at
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 5;
            """))
            
            print("\n👥 Últimos 5 usuários cadastrados:")
            for row in result:
                print(f"  - ID: {row[0]}")
                print(f"    Nome: {row[1]}")
                print(f"    Email: {row[2]}")
                print(f"    CPF: {row[3]}")
                print(f"    Tipo: {row[4]}")
                print(f"    Ativo: {'Sim' if row[5] else 'Não'}")
                print(f"    Criado: {row[6]}")
                print()
            
            # 6. Verificar duplicatas de CPF
            result = conn.execute(text("""
                SELECT cpf, COUNT(*) 
                FROM users 
                GROUP BY cpf 
                HAVING COUNT(*) > 1;
            """))
            
            duplicates = result.fetchall()
            if duplicates:
                print("⚠️  CPFs duplicados encontrados:")
                for row in duplicates:
                    print(f"  - CPF {row[0]}: {row[1]} registros")
            else:
                print("✅ Nenhum CPF duplicado encontrado")
            
            # 7. Verificar duplicatas de email
            result = conn.execute(text("""
                SELECT email, COUNT(*) 
                FROM users 
                GROUP BY email 
                HAVING COUNT(*) > 1;
            """))
            
            duplicates = result.fetchall()
            if duplicates:
                print("\n⚠️  Emails duplicados encontrados:")
                for row in duplicates:
                    print(f"  - Email {row[0]}: {row[1]} registros")
            else:
                print("✅ Nenhum email duplicado encontrado")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Verificando estado do banco de dados...")
    print("=" * 50)
    
    success = check_database()
    
    print("=" * 50)
    if success:
        print("✅ Verificação concluída!")
    else:
        print("❌ Verificação falhou!")
        sys.exit(1)