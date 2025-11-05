-- Migration: Sistema de Autenticação por CPF
-- Adiciona campo status na tabela users e cria novas tabelas para o sistema

-- 1. Adicionar campo status na tabela users (sem CHECK constraint para SQLite)
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'new';
ALTER TABLE users ADD COLUMN first_access_date TIMESTAMP;
ALTER TABLE users ADD COLUMN password_created_at TIMESTAMP;

-- 2. Tabela de Histórico de Senhas (password_history)
CREATE TABLE IF NOT EXISTS password_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Tabela de Logs de Email (email_logs)
CREATE TABLE IF NOT EXISTS email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'sent',
    temp_password VARCHAR(255),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Tabela de Logs de Acesso (access_logs)
CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. Criar índices para otimização
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf);
CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON password_history(user_id);
CREATE INDEX IF NOT EXISTS idx_password_history_created_at ON password_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_logs_user_id ON email_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_created_at ON access_logs(created_at DESC);

-- 6. Dados iniciais de exemplo para teste
INSERT OR IGNORE INTO users (cpf, email, name, status, is_active) VALUES
('12345678901', 'cliente1@example.com', 'Cliente Teste 1', 'new', 1),
('98765432100', 'cliente2@example.com', 'Cliente Teste 2', 'active', 1),
('11122233344', 'cliente3@example.com', 'Cliente Teste 3', 'reactivation', 1);

-- 7. Atualizar usuários existentes para ter status 'active' se já possuem senha
UPDATE users SET status = 'active' WHERE password IS NOT NULL;
UPDATE users SET status = 'new' WHERE password IS NULL;