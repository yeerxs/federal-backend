-- Adicionar campo device_type à tabela activations
-- Para suportar seleção de iPhone ou Android nas ativações Vivo eSIM

-- Criar enum para device_type se não existir
DO $$ BEGIN
    CREATE TYPE device_type_enum AS ENUM ('iphone', 'android');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Adicionar coluna device_type à tabela activations
ALTER TABLE activations 
ADD COLUMN IF NOT EXISTS device_type device_type_enum;

-- Comentário para documentação
COMMENT ON COLUMN activations.device_type IS 'Tipo de dispositivo para ativações