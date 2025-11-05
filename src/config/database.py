from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def init_database(app):
    """Inicializa a configuração do banco de dados"""
    
    # Verificar se deve usar SQLite para desenvolvimento
    use_sqlite = os.getenv('USE_SQLITE', 'true').lower() == 'true'
    
    if use_sqlite:
        # Configurar para usar SQLite
        database_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'federal_associados.db')
        database_url = f'sqlite:///{database_path}'
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        print(f"✅ Usando SQLite: {database_url}")
    else:
        # Configurar para usar Supabase PostgreSQL
        try:
            from .supabase_config import SupabaseConfig
            supabase_config = SupabaseConfig()
            app.config['SQLALCHEMY_DATABASE_URI'] = supabase_config.get_database_url()
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': 10,
                'pool_timeout': 20,
                'pool_recycle': -1,
                'pool_pre_ping': True
            }
            print("✅ Usando Supabase PostgreSQL")
        except Exception as e:
            print(f"⚠️ Erro ao configurar Supabase, usando SQLite: {e}")
            database_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'federal_associados.db')
            database_url = f'sqlite:///{database_path}'
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    
    return db

def create_tables(app):
    """Cria as tabelas do banco de dados"""
    with app.app_context():
        # Importar todos os modelos para garantir que sejam registrados
        from ..models.user import User, Activation, Document, DDD, ActivationHistory, AdminLog, Notification, SystemSetting, ContractAcceptance, Permission, UserPermission
        
        # Criar todas as tabelas
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")

def get_db():
    """Retorna a instância do banco de dados"""
    return db