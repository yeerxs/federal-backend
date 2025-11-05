-- Migração para adicionar Super Admin e sistema de permissões
-- Data: 2024-01-15

-- 1. Adicionar tipo 'super_admin' ao enum user_type
ALTER TYPE user_type_enum ADD VALUE 'super_admin';

-- 2. Criar tabela de permissões
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Criar tabela de relacionamento usuário-permissões
CREATE TABLE IF NOT EXISTS user_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) NOT NULL,
    permission_id UUID NOT NULL,
    granted_by VARCHAR(36),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id),
    UNIQUE(user_id, permission_id)
);

-- 4. Inserir permissões básicas do sistema
INSERT INTO permissions (name, description, category) VALUES
-- Gerenciamento de usuários
('manage_users', 'Criar, editar e excluir usuários', 'users'),
('view_users', 'Visualizar lista de usuários', 'users'),
('reset_user_passwords', 'Resetar senhas de usuários', 'users'),
('toggle_user_first_access', 'Forçar/remover primeiro acesso de usuários', 'users'),
('manage_user_permissions', 'Gerenciar permissões de outros usuários', 'users'),

-- Gerenciamento de ativações
('manage_activations', 'Aprovar, reprovar e gerenciar ativações', 'activations'),
('view_activations', 'Visualizar ativações', 'activations'),
('send_qr_codes', 'Enviar QR codes para ativações', 'activations'),
('view_activation_statistics', 'Visualizar estatísticas de ativações', 'activations'),

-- Gerenciamento de DDDs
('manage_ddds', 'Criar, editar e excluir DDDs', 'ddds'),
('view_ddds', 'Visualizar DDDs disponíveis', 'ddds'),

-- Dashboard e relatórios
('view_admin_dashboard', 'Acessar dashboard administrativo', 'dashboard'),
('view_detailed_statistics', 'Visualizar estatísticas detalhadas com gráficos', 'dashboard'),

-- Sistema
('view_admin_logs', 'Visualizar logs administrativos', 'system'),
('manage_system_settings', 'Gerenciar configurações do sistema', 'system');

-- 5. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_permission_id ON user_permissions(permission_id);
CREATE INDEX IF NOT EXISTS idx_permissions_category ON permissions(category);

-- 6. Criar função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 7. Criar trigger para atualizar updated_at na tabela permissions
CREATE TRIGGER update_permissions_updated_at 
    BEFORE UPDATE ON permissions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 8. Comentários nas tabelas
COMMENT ON TABLE permissions IS 'Tabela de permissões do sistema';
COMMENT ON TABLE user_permissions IS 'Relacionamento entre usuários e suas permissões';
COMMENT ON COLUMN permissions.category IS 'Categoria da permissão (users, activations, ddds, dashboard, system)';
COMMENT ON COLUMN user_permissions.granted_by IS 'ID do usuário que concedeu a permissão';
COMMENT ON COLUMN user_permissions.is_active IS 'Se a permissão está ativa para o usuário';