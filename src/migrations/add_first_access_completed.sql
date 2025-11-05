-- Adicionar campo first_access_completed à tabela users
ALTER TABLE users ADD COLUMN first_access_completed BOOLEAN DEFAULT FALSE;

-- Atualizar usuários admin existentes para marcar primeiro acesso como completo
UPDATE users SET first_access_completed = TRUE WHERE user_type = 'admin';

-- Comentário sobre a migração
COMMENT ON COLUMN users.first_access_completed IS 'Indica se o usuário completou o fluxo de primeiro acesso';