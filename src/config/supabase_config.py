import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class SupabaseConfig:
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # Só validar se não estiver usando SQLite
        use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'
        if not use_sqlite and (not self.url or not self.key):
            raise ValueError("SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidas nas variáveis de ambiente")
    
    def get_client(self) -> Client:
        """Retorna cliente Supabase para operações do usuário"""
        return create_client(self.url, self.key)
    
    def get_admin_client(self) -> Client:
        """Retorna cliente Supabase com privilégios administrativos"""
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY deve estar definida para operações administrativas")
        return create_client(self.url, self.service_role_key)
    
    def get_database_url(self) -> str:
        """Retorna URL de conexão PostgreSQL para SQLAlchemy"""
        db_host = os.getenv('SUPABASE_DB_HOST')
        db_port = os.getenv('SUPABASE_DB_PORT', '5432')
        db_name = os.getenv('SUPABASE_DB_NAME')
        db_user = os.getenv('SUPABASE_DB_USER')
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("Todas as variáveis de ambiente do banco devem estar definidas")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Instância global - só criar se não estiver usando SQLite
use_sqlite = os.getenv('USE_SQLITE', 'false').lower() == 'true'

if not use_sqlite:
    supabase_config = SupabaseConfig()
    supabase_client = supabase_config.get_client()
    supabase_admin = supabase_config.get_admin_client()
else:
    supabase_config = None
    supabase_client = None
    supabase_admin = None