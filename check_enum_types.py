#!/usr/bin/env python3

import psycopg2
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def check_enum_types():
    try:
        # Conectar ao banco
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'federal_associados'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'admin')
        )
        
        cursor = conn.cursor()
        
        print("🔍 Verificando tipos enum disponíveis...")
        
        # Verificar tipos enum existentes
        cursor.execute("""
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typname LIKE '%user_type%'
            ORDER BY t.typname, e.enumsortorder;
        """)
        
        enum_values = cursor.fetchall()
        
        if enum_values:
            print("\n📋 Valores do enum user_type_enum:")
            current_type = None
            for type_name, enum_value in enum_values:
                if current_type != type_name:
                    current_type = type_name
                    print(f"\n  Tipo: {type_name}")
                print(f"    - {enum_value}")
        else:
            print("❌ Nenhum enum user_type encontrado!")
            
        # Verificar se super_admin existe
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_enum e 
                JOIN pg_type t ON e.enumtypid = t.oid 
                WHERE t.typname = 'user_type_enum' AND e.enumlabel = 'super_admin'
            );
        """)
        
        has_super_admin = cursor.fetchone()[0]
        
        if has_super_admin:
            print("\n✅ O tipo 'super_admin' já existe no enum!")
        else:
            print("\n❌ O tipo 'super_admin' NÃO existe no enum!")
            print("💡 Será necessário adicionar 'super_admin' ao enum user_type_enum")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar enum: {e}")

if __name__ == "__main__":
    check_enum_types()