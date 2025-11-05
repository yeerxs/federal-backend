-- Migração para atualizar a tabela users com as colunas necessárias
-- Federal Associados - Sistema de Login e Primeiro Acesso

-- Adicionar colunas necessárias à tabela users
ALTER TABLE users ADD COLUMN cpf VARCHAR(11) UNIQUE;
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE users ADD COLUMN first_access_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN password_created_at TIMESTAMP;
ALTER TABLE users ADD COLUMN type VARCHAR(20) DEFAULT 'user';

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_type ON users(type);

-- Atualizar o admin existente com CPF e status
UPDATE users 
SET cpf = '12345678990', 
    status = 'active', 
    first_access_completed = TRUE,
    type = 'admin',
    password_created_at = datetime('now')
WHERE email = 'admin@federal.com';

-- Se não existir admin, criar um
INSERT OR IGNORE INTO users (
    email, 
    password_hash, 
    name, 
    role, 
    cpf, 
    status, 
    first_access_completed, 
    type,
    password_created_at,
    created_at
) VALUES (
    'admin@federal.com',
    'scrypt:32768:8:1$VQxQJQxQJQxQ$8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f',
    'Administrador Federal',
    'admin',
    '12345678990',
    'active',
    TRUE,
    'admin',
    datetime('now'),
    datetime('now')
);