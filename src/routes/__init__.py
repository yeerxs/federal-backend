# Arquivo __init__.py para tornar routes um módulo Python - Sistema Simplificado
from .auth import auth_bp
from .user import user_bp
from .admin import admin_bp
# from .contracts import contracts_bp  # Temporariamente comentado

__all__ = ['auth_bp', 'user_bp', 'admin_bp']  # 'contracts_bp' removido temporariamente