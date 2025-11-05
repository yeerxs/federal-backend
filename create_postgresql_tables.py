#!/usr/bin/env python3
"""
Script para criar todas as tabelas necessárias no PostgreSQL
Federal Associados - Sistema de Ativação
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def get_postgresql_connection():
    """Conecta ao PostgreSQL usando as variáveis de ambiente"""
    try:
        # Carregar variáveis do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        connection_params = {
            'host': os.getenv('SUPABASE_DB_HOST'),
            'port': os.getenv('SUPABASE_DB_PORT', 5432),
            'database': os.getenv('SUPABASE_DB_NAME'),
            'user': os.getenv('SUPABASE_DB_USER'),
            'password': os.getenv('SUPABASE_DB_PASSWORD'),
            'sslmode': 'require'
        }
        
        print(f"Conectando ao PostgreSQL: {connection_params['host']}:{connection_params['port']}/{connection_params['database']}")
        
        conn = psycopg2.connect(**connection_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
        
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

def create_enums(cursor):
    """Criar os tipos ENUM necessários"""
    enums = [
        "CREATE TYPE user_type_enum AS ENUM ('cliente', 'admin', 'operador');",
        "CREATE TYPE operator_enum AS ENUM ('vivo', 'claro', 'tim');",
        "CREATE TYPE chip_type_enum AS ENUM ('fisico', 'esim');",
        "CREATE TYPE device_type_enum AS ENUM ('iphone', 'android');",
        "CREATE TYPE service_type_enum AS ENUM ('pos_pago', 'pre_pago', 'controle');",
        "CREATE TYPE activation_status_enum AS ENUM ('pendente_contrato', 'pendente_documentos', 'pendente_dados_tecnicos', 'pendente_analise_documentos', 'documentos_rejeitados', 'em_analise', 'aprovado', 'reprovado', 'pendente_confirmacao_qr', 'ativada', 'cancelado');",
        "CREATE TYPE document_type_enum AS ENUM ('identity_front', 'identity_back', 'selfie_with_document', 'qr_code_esim', 'combined_contract');",
        "CREATE TYPE document_status_enum AS ENUM ('pending', 'approved', 'rejected');",
        "CREATE TYPE notification_type_enum AS ENUM ('email', 'push', 'system');",
        "CREATE TYPE pdf_job_status_enum AS ENUM ('pending', 'processing', 'completed', 'failed');"
    ]
    
    for enum_sql in enums:
        try:
            cursor.execute(enum_sql)
            print(f"✓ ENUM criado: {enum_sql.split()[2]}")
        except psycopg2.errors.DuplicateObject:
            print(f"⚠ ENUM já existe: {enum_sql.split()[2]}")
        except Exception as e:
            print(f"✗ Erro ao criar ENUM: {e}")

def create_tables(cursor):
    """Criar todas as tabelas necessárias"""
    
    # Tabela users
    users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        cpf VARCHAR(11) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        user_type user_type_enum NOT NULL DEFAULT 'cliente',
        name VARCHAR(255) NOT NULL,
        phone VARCHAR(20),
        address VARCHAR(500),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        last_login TIMESTAMP WITH TIME ZONE,
        failed_login_attempts INTEGER DEFAULT 0,
        locked_until TIMESTAMP WITH TIME ZONE,
        first_access_completed BOOLEAN DEFAULT FALSE,
        identity_front_path VARCHAR(500),
        identity_back_path VARCHAR(500),
        selfie_with_document_path VARCHAR(500),
        combined_pdf_path VARCHAR(500),
        documents_uploaded_at TIMESTAMP WITH TIME ZONE,
        documents_approved BOOLEAN DEFAULT FALSE,
        documents_approved_at TIMESTAMP WITH TIME ZONE,
        documents_approved_by UUID REFERENCES users(id)
    );
    """
    
    # Tabela contract_acceptances
    contract_acceptances_table = """
    CREATE TABLE IF NOT EXISTS contract_acceptances (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id),
        cpf VARCHAR(11) NOT NULL,
        security_token VARCHAR(128) NOT NULL UNIQUE,
        ip_address VARCHAR(45) NOT NULL,
        user_agent TEXT,
        accepted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
        contract_version VARCHAR(50) DEFAULT '1.0',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabela activations
    activations_table = """
    CREATE TABLE IF NOT EXISTS activations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id),
        operator operator_enum NOT NULL,
        chip_type chip_type_enum NOT NULL,
        ddd VARCHAR(2) NOT NULL,
        iccid VARCHAR(50),
        eid VARCHAR(50),
        imei VARCHAR(50),
        device_type device_type_enum,
        service_type service_type_enum,
        status activation_status_enum DEFAULT 'pendente_contrato',
        contract_accepted BOOLEAN DEFAULT FALSE,
        contract_accepted_at TIMESTAMP WITH TIME ZONE,
        contract_ip VARCHAR(45),
        contract_acceptance_id UUID REFERENCES contract_acceptances(id),
        documents_uploaded_at TIMESTAMP WITH TIME ZONE,
        technical_data_completed_at TIMESTAMP WITH TIME ZONE,
        approved_at TIMESTAMP WITH TIME ZONE,
        approved_by UUID REFERENCES users(id),
        qr_code_path VARCHAR(500),
        qr_scanned_at TIMESTAMP WITH TIME ZONE,
        line_number VARCHAR(20),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabela documents
    documents_table = """
    CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        activation_id UUID NOT NULL REFERENCES activations(id),
        user_id UUID NOT NULL REFERENCES users(id),
        document_type document_type_enum NOT NULL,
        file_path VARCHAR(500) NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type VARCHAR(100) NOT NULL,
        status document_status_enum DEFAULT 'pending',
        uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        is_approved BOOLEAN,
        approved_by UUID REFERENCES users(id),
        approved_at TIMESTAMP WITH TIME ZONE,
        reviewed_at TIMESTAMP WITH TIME ZONE,
        reviewed_by UUID REFERENCES users(id),
        rejection_reason TEXT
    );
    """
    
    # Tabela ddds
    ddds_table = """
    CREATE TABLE IF NOT EXISTS ddds (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        operator operator_enum NOT NULL,
        ddd VARCHAR(2) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_by UUID REFERENCES users(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(operator, ddd)
    );
    """
    
    # Tabela activation_history
    activation_history_table = """
    CREATE TABLE IF NOT EXISTS activation_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        activation_id UUID NOT NULL REFERENCES activations(id),
        previous_status activation_status_enum,
        new_status activation_status_enum NOT NULL,
        changed_by UUID NOT NULL REFERENCES users(id),
        change_reason TEXT,
        changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabela admin_logs
    admin_logs_table = """
    CREATE TABLE IF NOT EXISTS admin_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id),
        action VARCHAR(255) NOT NULL,
        resource_type VARCHAR(100),
        resource_id VARCHAR(100),
        details TEXT,
        ip_address VARCHAR(45),
        user_agent TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabela notifications
    notifications_table = """
    CREATE TABLE IF NOT EXISTS notifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id),
        activation_id UUID REFERENCES activations(id),
        type notification_type_enum NOT NULL,
        title VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        sent_at TIMESTAMP WITH TIME ZONE,
        read_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabela system_settings
    system_settings_table = """
    CREATE TABLE IF NOT EXISTS system_settings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        key VARCHAR(100) UNIQUE NOT NULL,
        value TEXT,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabela generated_pdfs
    generated_pdfs_table = """
    CREATE TABLE IF NOT EXISTS generated_pdfs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id),
        activation_id UUID NOT NULL REFERENCES activations(id),
        file_name VARCHAR(255) NOT NULL,
        file_path VARCHAR(500) NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type VARCHAR(100) DEFAULT 'application/pdf',
        document_hash VARCHAR(64),
        included_documents JSONB,
        contract_text_included BOOLEAN DEFAULT TRUE,
        digital_signature_ready BOOLEAN DEFAULT TRUE,
        download_count INTEGER DEFAULT 0,
        last_downloaded_at TIMESTAMP WITH TIME ZONE,
        expires_at TIMESTAMP WITH TIME ZONE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabela pdf_generation_jobs
    pdf_generation_jobs_table = """
    CREATE TABLE IF NOT EXISTS pdf_generation_jobs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id),
        activation_id UUID NOT NULL REFERENCES activations(id),
        status pdf_job_status_enum DEFAULT 'pending',
        progress INTEGER DEFAULT 0,
        error_message TEXT,
        selected_documents JSONB,
        generated_pdf_id UUID REFERENCES generated_pdfs(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE
    );
    """
    
    # Tabela tokens (para o sistema de verificação de hash)
    tokens_table = """
    CREATE TABLE IF NOT EXISTS tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        cpf VARCHAR(11) NOT NULL,
        email VARCHAR(255) NOT NULL,
        token VARCHAR(500) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP WITH TIME ZONE,
        used_at TIMESTAMP WITH TIME ZONE,
        is_active BOOLEAN DEFAULT TRUE
    );
    """
    
    tables = [
        ("users", users_table),
        ("contract_acceptances", contract_acceptances_table),
        ("activations", activations_table),
        ("documents", documents_table),
        ("ddds", ddds_table),
        ("activation_history", activation_history_table),
        ("admin_logs", admin_logs_table),
        ("notifications", notifications_table),
        ("system_settings", system_settings_table),
        ("generated_pdfs", generated_pdfs_table),
        ("pdf_generation_jobs", pdf_generation_jobs_table),
        ("tokens", tokens_table)
    ]
    
    for table_name, table_sql in tables:
        try:
            cursor.execute(table_sql)
            print(f"✓ Tabela criada: {table_name}")
        except Exception as e:
            print(f"✗ Erro ao criar tabela {table_name}: {e}")

def create_indexes(cursor):
    """Criar índices para melhor performance"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type);",
        "CREATE INDEX IF NOT EXISTS idx_activations_user_id ON activations(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_activations_status ON activations(status);",
        "CREATE INDEX IF NOT EXISTS idx_documents_activation_id ON documents(activation_id);",
        "CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_tokens_cpf ON tokens(cpf);",
        "CREATE INDEX IF NOT EXISTS idx_tokens_email ON tokens(email);",
        "CREATE INDEX IF NOT EXISTS idx_tokens_created_at ON tokens(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_admin_logs_user_id ON admin_logs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON admin_logs(created_at);"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            index_name = index_sql.split()[5]  # Extrair nome do índice
            print(f"✓ Índice criado: {index_name}")
        except Exception as e:
            print(f"✗ Erro ao criar índice: {e}")

def insert_admin_user(cursor):
    """Inserir usuário admin padrão"""
    admin_sql = """
    INSERT INTO users (
        cpf, email, password_hash, user_type, name, 
        is_active, first_access_completed, created_at
    ) VALUES (
        '12345678990', 
        'admin@federal.com', 
        'scrypt:32768:8:1$VQxQJQxQJQxQ$8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f',
        'admin',
        'Administrador Federal',
        TRUE,
        TRUE,
        CURRENT_TIMESTAMP
    ) ON CONFLICT (email) DO NOTHING;
    """
    
    try:
        cursor.execute(admin_sql)
        print("✓ Usuário admin criado/verificado")
    except Exception as e:
        print(f"✗ Erro ao criar usuário admin: {e}")

def main():
    """Função principal"""
    print("=== Criação de Tabelas PostgreSQL - Federal Associados ===")
    print(f"Iniciado em: {datetime.now()}")
    print()
    
    # Conectar ao PostgreSQL
    conn = get_postgresql_connection()
    if not conn:
        print("✗ Falha na conexão com PostgreSQL")
        return False
    
    try:
        cursor = conn.cursor()
        
        print("1. Criando ENUMs...")
        create_enums(cursor)
        print()
        
        print("2. Criando tabelas...")
        create_tables(cursor)
        print()
        
        print("3. Criando índices...")
        create_indexes(cursor)
        print()
        
        print("4. Inserindo usuário admin...")
        insert_admin_user(cursor)
        print()
        
        print("✓ Migração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"✗ Erro durante a migração: {e}")
        return False
        
    finally:
        if conn:
            conn.close()
            print("Conexão PostgreSQL fechada.")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)