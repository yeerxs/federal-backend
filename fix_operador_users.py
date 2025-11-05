#!/usr/bin/env python3
"""
Script para corrigir usuários com tipo 'operador' no banco de dados
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def fix_operador_users():
    """Corrigir usuários com tipo 'operador'"""
    
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
            
            # 1. Verificar usuários com tipo 'operador'
            result = conn.execute(text("""
                SELECT id, name, email, cpf, user_type 
                FROM users 
                WHERE user_type = 'operador';
            """))
            
            operador_users = result.fetchall()
            
            if not operador_users:
                print("✅ Nenhum usuário com tipo 'operador' encontrado!")
                return True
            
            print(f"⚠️  Encontrados {len(operador_users)} usuários com tipo 'operador':")
            for user in operador_users:
                print(f"  - ID: {user[0]}")
                print(f"    Nome: {user[1]}")
                print(f"    Email: {user[2]}")
                print(f"    CPF: {user[3]}")
                print()
            
            # 2. Converter automaticamente para 'admin' (decisão automática)
            print("🔄 Convertendo usuários 'operador' para 'admin'...")
            
            result = conn.execute(text("""
                UPDATE users 
                SET user_type = 'admin' 
                WHERE user_type = 'operador';
            """))
            conn.commit()
            print(f"✅ {len(operador_users)} usuários convertidos para 'admin'!")
            
            # 3. Verificar se ainda existem usuários 'operador'
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM users 
                WHERE user_type = 'operador';
            """))
            
            remaining = result.fetchone()[0]
            
            if remaining == 0:
                print("✅ Todos os usuários 'operador' foram corrigidos!")
                
                # 4. Mostrar estatísticas atualizadas
                result = conn.execute(text("""
                    SELECT user_type, COUNT(*) 
                    FROM users 
                    GROUP BY user_type 
                    ORDER BY user_type;
                """))
                
                print("\n📊 Usuários por tipo (atualizado):")
                for row in result:
                    print(f"  - {row[0]}: {row[1]} usuários")
                
                return True
            else:
                print(f"⚠️  Ainda existem {remaining} usuários 'operador'!")
                return False
            
    except Exception as e:
        print(f"❌ Erro ao corrigir usuários: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Corrigindo usuários com tipo 'operador'...")
    print("=" * 50)
    
    success = fix_operador_users()
    
    print("=" * 50)
    if success:
        print("✅ Correção concluída!")
    else:
        print("❌ Correção falhou!")
        sys.exit(1)