-- Adicionar campo address à tabela users
ALTER TABLE users ADD COLUMN address VARCHAR(500);

-- Comentário sobre a alteração
COMMENT ON COLUMN users.address IS 'Endereço completo do usuário';