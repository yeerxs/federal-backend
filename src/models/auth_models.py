from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
import uuid
import secrets
import random
import string
from config.database import db

class VerificationCode(db.Model):
    """Modelo para códigos de verificação por email"""
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=True)
    identifier = db.Column(db.String(255), nullable=False)  # Email ou CPF
    code = db.Column(db.String(6), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    @staticmethod
    def generate_code():
        """Gera um código de 6 dígitos"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def create_verification_code(identifier, email, expiry_minutes=15):
        """Cria um novo código de verificação"""
        code = VerificationCode.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        
        verification_code = VerificationCode(
            identifier=identifier,
            code=code,
            email=email,
            expires_at=expires_at
        )
        
        return verification_code
    
    def is_expired(self):
        """Verifica se o código expirou"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Verifica se o código é válido (não usado e não expirado)"""
        return not self.used and not self.is_expired()
    
    def mark_as_used(self):
        """Marca o código como usado"""
        self.used = True
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'identifier': self.identifier,
            'code': self.code,
            'email': self.email,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid()
        }

class ContractValidation(db.Model):
    """Modelo para validações de contrato via API de parceiros"""
    __tablename__ = 'contract_validations'
    
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=True)
    identifier = db.Column(db.String(255), nullable=False)  # Email ou CPF
    approved = db.Column(db.Boolean, nullable=False)
    partner_response = db.Column(db.Text)  # Resposta da API do parceiro
    partner_api_called_at = db.Column(db.DateTime(timezone=True))
    validation_details = db.Column(db.Text)  # JSON com detalhes
    validated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    @staticmethod
    def create_validation(identifier, approved, partner_response=None, validation_details=None):
        """Cria uma nova validação de contrato"""
        validation = ContractValidation(
            identifier=identifier,
            approved=approved,
            partner_response=partner_response,
            partner_api_called_at=datetime.utcnow(),
            validation_details=validation_details
        )
        
        return validation
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'identifier': self.identifier,
            'approved': self.approved,
            'partner_response': self.partner_response,
            'partner_api_called_at': self.partner_api_called_at.isoformat() if self.partner_api_called_at else None,
            'validation_details': self.validation_details,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TemporarySession(db.Model):
    """Modelo para sessões temporárias durante o processo de primeiro acesso"""
    __tablename__ = 'temporary_sessions'
    
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    identifier = db.Column(db.String(255), nullable=False)  # Email ou CPF
    session_token = db.Column(db.String(128), nullable=False, unique=True)
    session_type = db.Column(db.String(50), nullable=False)  # 'password_creation', 'password_reset'
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    @staticmethod
    def generate_session_token():
        """Gera um token de sessão seguro"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def create_session(identifier, session_type, expiry_minutes=30):
        """Cria uma nova sessão temporária"""
        session_token = TemporarySession.generate_session_token()
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        
        session = TemporarySession(
            identifier=identifier,
            session_token=session_token,
            session_type=session_type,
            expires_at=expires_at
        )
        
        return session
    
    def is_expired(self):
        """Verifica se a sessão expirou"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Verifica se a sessão é válida (não usada e não expirada)"""
        return not self.used and not self.is_expired()
    
    def mark_as_used(self):
        """Marca a sessão como usada"""
        self.used = True
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'identifier': self.identifier,
            'session_token': self.session_token,
            'session_type': self.session_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid()
        }

class SystemConfig(db.Model):
    """Modelo para configurações do sistema"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_config(key, default_value=None):
        """Obtém uma configuração do sistema"""
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else default_value
    
    @staticmethod
    def set_config(key, value, description=None):
        """Define uma configuração do sistema"""
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
            if description:
                config.description = description
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(key=key, value=value, description=description)
            db.session.add(config)
        
        db.session.commit()
        return config
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }