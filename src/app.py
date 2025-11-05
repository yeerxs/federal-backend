from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Importar configuração do banco de dados
from config.database import init_database

def create_app():
    app = Flask(__name__)
    
    # Configurações básicas
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'federal-associados-secret-key-2024')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Inicializar banco de dados
    init_database(app)
    
    # Configurar CORS para permitir requisições do frontend
    CORS(app, origins=[
        "http://localhost:3000",  # Porta atual do frontend
        "http://127.0.0.1:3000",
        "http://localhost:3002",  # Porta alternativa do frontend
        "http://127.0.0.1:3002",
        "http://localhost:5173",  # Vite dev server alternativo
        "http://127.0.0.1:5173"
    ], supports_credentials=True, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])
    
    # Inicializar JWT
    jwt = JWTManager(app)
    
    # Registrar blueprints - Sistema Simplificado
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.admin import admin_bp
    # from routes.contracts import contracts_bp  # Temporariamente comentado
    from routes.client import client_bp
    from routes.activation import activation_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    # app.register_blueprint(contracts_bp, url_prefix='/api')  # Temporariamente comentado
    app.register_blueprint(client_bp, url_prefix='/api/client')
    app.register_blueprint(activation_bp, url_prefix='/api/activations')
    
    # Criar diretório de uploads se não existir
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # Rota de teste para verificar se o servidor está funcionando
    # Adicionar antes do return app
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {'status': 'ok', 'message': 'Backend está funcionando!'}
    
    return app

# Criar instância da aplicação
app = create_app()

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    app.run(host='0.0.0.0', port=5000, debug=True)