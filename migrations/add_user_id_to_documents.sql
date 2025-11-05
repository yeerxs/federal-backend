-- Migração para adicionar coluna user_id à tabela documents
-- Esta coluna é necessária para o relacionamento entre documentos e usuários

-- Adicionar a coluna user_id
ALTER TABLE documents ADD COLUMN user_id TEXT;

-- Criar índice para melhor performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);

-- Atualizar registros existentes para definir user_id baseado na ativação
-- Buscar o user_id através da tabela activations
UPDATE documents 
SET user_id = (
    SELECT a.user_id 
    FROM activations a 
    WHERE a.id = documents.activation_id
)
WHERE user_id IS NULL;

-- Tornar a coluna NOT NULL após popular os dados
-- Nota: SQLite não suporta ALTER COLUMN, então vamos recriar a tabela

-- Criar tabela temporária com a estrutura correta
CREATE TABLE documents_new (
    id TEXT PRIMARY KEY,
    activation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    document_type VARCHAR(20) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    uploaded_at DATETIME,
    is_approved BOOLEAN,
    approved_by TEXT,
    approved_at DATETIME,
    rejection_reason TEXT,
    FOREIGN KEY (activation_id) REFERENCES activations(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- Copiar dados da tabela original
INSERT INTO documents_new (
    id, activation_id, user_id, document_type, file_path, file_name, 
    file_size, mime_type, uploaded_at, is_approved, approved_by, 
    approved_at, rejection_reason
)
SELECT 
    id, activation_id, user_id, document_type, file_path, file_name,
    file_size, mime_type, uploaded_at, is_approved, approved_by,
    approved_at, rejection_reason
FROM documents;

-- Remover tabela original
DROP TABLE documents;

-- Renomear tabela nova
ALTER TABLE documents_new RENAME TO documents;

-- Recriar índices
CREATE INDEX IF NOT EXISTS idx_documents_activation_id ON documents(activation_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_approved_by ON documents(approved_by);