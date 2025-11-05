-- Migração para adicionar o status 'documentos_rejeitados' ao enum de status de ativação
-- Data: 2024-01-20
-- Descrição: Adiciona o status 'documentos_rejeitados' para permitir reenvio de documentos rejeitados

-- Adicionar o novo valor ao enum activation_status_enum
ALTER TYPE activation_status_enum ADD VALUE 'documentos_rejeitados';

-- Comentário para documentar a mudança
COMMENT ON TYPE activation_status_enum IS 'Status possíveis para ativações: pendente_contrato, pendente_documentos, pendente_dados_tecnicos, pendente_analise_documentos, documentos_rejeitados, em_analise, aprovado, reprovado, pendente_confirmacao_qr, ativada, cancelado';