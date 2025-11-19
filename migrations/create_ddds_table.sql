-- Migration para criar tabela de DDDs
-- Created: $(date)

CREATE TABLE IF NOT EXISTS ddds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ddd VARCHAR(2) NOT NULL,
    operadora VARCHAR(100) NOT NULL,
    tipo_chip VARCHAR(50) NOT NULL,
    especificacao VARCHAR(50) NOT NULL,
    linha_original VARCHAR(20) NOT NULL,
    arquivo_origem VARCHAR(255) NOT NULL,
    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hash_linha VARCHAR(64) UNIQUE NOT NULL
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_ddd ON ddds(ddd);
CREATE INDEX IF NOT EXISTS idx_operadora ON ddds(operadora);
CREATE INDEX IF NOT EXISTS idx_tipo_chip ON ddds(tipo_chip);
CREATE INDEX IF NOT EXISTS idx_data_importacao ON ddds(data_importacao);