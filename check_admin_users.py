#!/usr/bin/env python3
"""
Script para verificar usuários admin disponíveis
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def check_admin_users():
    """Verificar usuários admin disponíveis"""
    
    # Configuração do banco
    database_url = os.getenv('POSTGRESQL_URL')
    if not database_url:
        print("❌ POSTGRESQL_URL não encontrada no .env")
        return False
    
    print(f"🔗 Conectando ao banco de dados...")
    
    try:
        # Criar conexão
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("✅ Conexão estabelecida com sucesso!")
            
            # 1. Verificar tipos de usuário disponíveis
            result = conn.execute(text("""
                SELECT DISTINCT user_type 
                FROM users 
                ORDER BY user_type;
            """))
            
            user_types = [row[0] for row in result.fetchall()]
            print(f"\n📋 Tipos de usuário disponíveis: {', '.join(user_types)}")
            
            # 2. Verificar usuários admin
            result = conn.execute(text("""
                SELECT id, name, email, cpf, is_active, created_at
                FROM users 
                WHERE user_type = 'admin'
                ORDER BY created_at DESC;
            """))
            
            admins = result.fetchall()
            
            if admins:
                print(f"\n👑 Administradores encontrados ({len(admins)}):")
                print("=" * 60)
                
                for i, admin in enumerate(admins, 1):
                    print(f"\n{i}. Administrador:")
                    print(f"   📧 Email: {admin[2]}")
                    print(f"   👤 Nome: {admin[1]}")
                    print(f"   🆔 CPF: {admin[3]}")
                    print(f"   ✅ Status: {'Ativo' if admin[4] else 'Inativo'}")
                    print(f"   📅 Criado: {admin[5]}")
                
                print(f"\n🎯 CREDENCIAIS DE LOGIN (Admin):")
                print("=" * 50)
                print(f"📧 Email: {admins[0][2]}")
                print(f"🔑 Senha: admin123 (padrão)")
                print("=" * 50)
                print("\n💡 Use essas credenciais para fazer login como administrador")
                
                return True
            
            else:
                print("\n⚠️  Nenhum administrador encontrado!")
                
                # Verificar se existe algum usuário
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                total_users = result.fetchone()[0]
                
                if total_users > 0:
                    print("📋 Listando todos os usuários disponíveis:")
                    result = conn.execute(text("""
                        SELECT name, email, user_type, is_active
                        FROM users 
                        ORDER BY created_at DESC;
                    """))
                    
                    all_users = result.fetchall()
                    for i, user in enumerate(all_users, 1):
                        print(f"   {i}. {user[1]} ({user[0]}) - Tipo: {user[2]} - {'Ativo' if user[3] else 'Inativo'}")
                
                return False
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print("👑 Verificando usuários administradores...")
    print("=" * 60)
    
    success = check_admin_users()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Verificação concluída!")
    else:
        print("❌ Nenhum administrador encontrado!")