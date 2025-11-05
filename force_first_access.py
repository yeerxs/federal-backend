#!/usr/bin/env python3
"""
Script para forçar o primeiro acesso de usuários específicos
Atualiza o campo first_access_completed = TRUE para os emails especificados
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def get_db_connection():
    """Conecta ao banco PostgreSQL usando as credenciais do .env"""
    try:
        connection = psycopg2.connect(
            host=os.getenv('SUPABASE_DB_HOST'),
            database=os.getenv('SUPABASE_DB_NAME'),
            user=os.getenv('SUPABASE_DB_USER'),
            password=os.getenv('SUPABASE_DB_PASSWORD'),
            port=os.getenv('SUPABASE_DB_PORT', 5432),
            sslmode='require'
        )
        return connection
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

def check_users_exist(cursor, emails):
    """Verifica quais usuários existem no banco"""
    try:
        query = """
        SELECT email, name, first_access_completed 
        FROM users 
        WHERE email = ANY(%s)
        """
        cursor.execute(query, (emails,))
        results = cursor.fetchall()
        
        print(f"\n🔍 Verificando usuários no banco:")
        found_emails = []
        
        for email, name, first_access in results:
            status = "✅ Já completou" if first_access else "❌ Não completou"
            print(f"  • {email} ({name}) - Primeiro acesso: {status}")
            found_emails.append(email)
        
        missing_emails = set(emails) - set(found_emails)
        if missing_emails:
            print(f"\n⚠️  Usuários não encontrados:")
            for email in missing_emails:
                print(f"  • {email}")
        
        return found_emails, missing_emails
        
    except Exception as e:
        print(f"❌ Erro ao verificar usuários: {e}")
        return [], emails

def force_first_access(cursor, emails):
    """Força o primeiro acesso para os usuários especificados"""
    try:
        query = """
        UPDATE users 
        SET first_access_completed = TRUE,
            updated_at = CURRENT_TIMESTAMP
        WHERE email = ANY(%s) AND first_access_completed = FALSE
        RETURNING email, name
        """
        
        cursor.execute(query, (emails,))
        updated_users = cursor.fetchall()
        
        print(f"\n🔄 Atualizando primeiro acesso:")
        if updated_users:
            for email, name in updated_users:
                print(f"  ✅ {email} ({name}) - Primeiro acesso forçado com sucesso")
        else:
            print("  ℹ️  Nenhum usuário foi atualizado (já tinham primeiro acesso completo)")
        
        return len(updated_users)
        
    except Exception as e:
        print(f"❌ Erro ao atualizar usuários: {e}")
        return 0

def verify_changes(cursor, emails):
    """Verifica se as alterações foram aplicadas corretamente"""
    try:
        query = """
        SELECT email, name, first_access_completed, updated_at
        FROM users 
        WHERE email = ANY(%s)
        ORDER BY email
        """
        
        cursor.execute(query, (emails,))
        results = cursor.fetchall()
        
        print(f"\n✅ Verificação final:")
        all_completed = True
        
        for email, name, first_access, updated_at in results:
            status = "✅ Completado" if first_access else "❌ Não completado"
            print(f"  • {email} ({name}) - Status: {status} - Atualizado: {updated_at}")
            if not first_access:
                all_completed = False
        
        return all_completed
        
    except Exception as e:
        print(f"❌ Erro ao verificar alterações: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando processo de forçar primeiro acesso...")
    
    # Emails dos usuários para forçar primeiro acesso
    target_emails = ['camila@example.com', 'isaac@example.com']
    
    print(f"\n📧 Usuários alvo:")
    for email in target_emails:
        print(f"  • {email}")
    
    # Conectar ao banco
    connection = get_db_connection()
    if not connection:
        print("❌ Não foi possível conectar ao banco de dados")
        sys.exit(1)
    
    try:
        cursor = connection.cursor()
        
        # 1. Verificar se os usuários existem
        found_emails, missing_emails = check_users_exist(cursor, target_emails)
        
        if not found_emails:
            print("\n❌ Nenhum usuário encontrado no banco")
            return
        
        # 2. Forçar primeiro acesso para usuários encontrados
        updated_count = force_first_access(cursor, found_emails)
        
        # 3. Confirmar alterações
        connection.commit()
        print(f"\n💾 Alterações salvas no banco ({updated_count} usuários atualizados)")
        
        # 4. Verificar se as alterações foram aplicadas
        success = verify_changes(cursor, found_emails)
        
        if success:
            print(f"\n🎉 Processo concluído com sucesso!")
            print(f"   • {len(found_emails)} usuários processados")
            print(f"   • {updated_count} usuários atualizados")
            if missing_emails:
                print(f"   • {len(missing_emails)} usuários não encontrados")
        else:
            print(f"\n⚠️  Processo concluído com problemas")
        
    except Exception as e:
        print(f"❌ Erro durante o processo: {e}")
        connection.rollback()
    
    finally:
        cursor.close()
        connection.close()
        print("\n🔌 Conexão com banco encerrada")

if __name__ == "__main__":
    main()