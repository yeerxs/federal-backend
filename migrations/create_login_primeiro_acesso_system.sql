-- Migração para Sistema de Login e Primeiro Acesso
-- Federal Associados - Sistema Unificado de Autenticação
-- Data: 2024

-- 1. Adicionar campos necessários na tabela users (se não existirem)
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_access_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_created_at TIMESTAMP;

-- 2. Tabela de Códigos de Verificação (verification_codes)
CREATE TABLE IF NOT EXISTS verification_codes (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT,
    identifier VARCHAR(255) NOT NULL, -- Email ou CPF usado para solicitar o código
    code VARCHAR(6) NOT NULL,
    email VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Tabela de Validações de Contrato (contract_validations)
CREATE TABLE IF NOT EXISTS contract_validations (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT,
    identifier VARCHAR(255) NOT NULL, -- Email ou CPF validado
    approved BOOLEAN NOT NULL,
    partner_response TEXT, -- Resposta da API do parceiro
    partner_api_called_at TIMESTAMP,
    validation_details TEXT, -- JSON com detalhes da validação
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Tabela de Sessões Temporárias (temporary_sessions)
CREATE TABLE IF NOT EXISTS temporary_sessions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    identifier VARCHAR(255) NOT NULL, -- Email ou CPF
    session_token VARCHAR(128) NOT NULL UNIQUE,
    session_type VARCHAR(50) NOT NULL, -- 'password_creation', 'password_reset'
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabela de Configurações do Sistema (system_config)
CREATE TABLE IF NOT EXISTS system_config (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Índices para performance
CREATE INDEX IF NOT EXISTS idx_verification_codes_identifier ON verification_codes(identifier);
CREATE INDEX IF NOT EXISTS idx_verification_codes_code ON verification_codes(code);
CREATE INDEX IF NOT EXISTS idx_verification_codes_expires_at ON verification_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_verification_codes_used ON verification_codes(used);

CREATE INDEX IF NOT EXISTS idx_contract_validations_identifier ON contract_validations(identifier);
CREATE INDEX IF NOT EXISTS idx_contract_validations_approved ON contract_validations(approved);
CREATE INDEX IF NOT EXISTS idx_contract_validations_user_id ON contract_validations(user_id);

CREATE INDEX IF NOT EXISTS idx_temporary_sessions_token ON temporary_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_temporary_sessions_expires_at ON temporary_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_temporary_sessions_identifier ON temporary_sessions(identifier);

CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 7. Configurações iniciais do sistema
INSERT OR REPLACE INTO system_config (key, value, description) VALUES 
('partner_api_url', 'https://api.parceiro.com/contracts', 'URL da API do parceiro para validação de contratos'),
('partner_api_key', 'sua_chave_api_aqui', 'Chave de API para autenticação com o parceiro'),
('email_verification_expiry_minutes', '15', 'Tempo de expiração dos códigos de verificação em minutos'),
('password_min_length', '8', 'Comprimento mínimo da senha'),
('max_login_attempts', '5', 'Número máximo de tentativas de login'),
('account_lockout_minutes', '30', 'Tempo de bloqueio da conta em minutos após exceder tentativas'),
('smtp_server', 'smtp.gmail.com', 'Servidor SMTP para envio de emails'),
('smtp_port', '587', 'Porta do servidor SMTP'),
('smtp_username', '', 'Usuário do SMTP'),
('smtp_password', '', 'Senha do SMTP'),
('smtp_use_tls', 'true', 'Usar TLS no SMTP'),
('system_email_from', 'noreply@federalassociados.com', 'Email remetente do sistema');

-- 8. Trigger para atualizar updated_at em system_config
CREATE TRIGGER IF NOT EXISTS update_system_config_timestamp 
    AFTER UPDATE ON system_config
    FOR EACH ROW
BEGIN
    UPDATE system_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 9. Função de limpeza automática de códigos expirados (será executada via script Python)
-- Esta será implementada no backend Python, não no SQLite

-- 10. Atualizar status do admin existente
UPDATE users SET status = 'active', first_access_completed = TRUE 
WHERE cpf = '12345678990' AND email = 'admin@federal.com';

-- 11. Verificar se existem usuários sem status definido e definir como 'pending'
UPDATE users SET status = 'pending' WHERE status IS NULL;
UPDATE users SET first_access_completed = FALSE WHERE first_access_completed IS NULL;