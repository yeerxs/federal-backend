from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid
import secrets
from config.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    # Usar String para SQLite, UUID para PostgreSQL
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum('cliente', 'admin', 'super_admin', name='user_type_enum'), nullable=False, default='cliente')
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime(timezone=True))
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime(timezone=True))
    first_access_completed = db.Column(db.Boolean, default=False)
    
    # Documentos do perfil
    identity_front_path = db.Column(db.String(500))
    identity_back_path = db.Column(db.String(500))
    selfie_with_document_path = db.Column(db.String(500))
    combined_pdf_path = db.Column(db.String(500))
    documents_uploaded_at = db.Column(db.DateTime(timezone=True))
    documents_approved = db.Column(db.Boolean, default=False)
    documents_approved_at = db.Column(db.DateTime(timezone=True))
    documents_approved_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # Relacionamentos
    activations = db.relationship('Activation', foreign_keys='Activation.user_id', backref='user', lazy=True)
    approved_activations = db.relationship('Activation', foreign_keys='Activation.approved_by', backref='approver', lazy=True)
    admin_logs = db.relationship('AdminLog', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    created_ddds = db.relationship('DDD', backref='creator', lazy=True)
    approved_documents = db.relationship('Document', foreign_keys='Document.approved_by', backref='approver', lazy=True)
    reviewed_documents = db.relationship('Document', foreign_keys='Document.reviewed_by', backref='reviewer', lazy=True)
    activation_changes = db.relationship('ActivationHistory', backref='changer', lazy=True)
    contract_acceptances = db.relationship('ContractAcceptance', backref='user', lazy=True)
    
    def has_permission(self, permission_name):
        """Verifica se o usuário tem uma permissão específica"""
        if self.user_type == 'super_admin':
            return True  # Super admin tem todas as permissões
        
        # Verificar permissões específicas do usuário
        for user_perm in self.user_permissions:
            if user_perm.is_active and user_perm.permission.name == permission_name:
                return True
        return False
    
    def get_permissions(self):
        """Retorna lista de permissões ativas do usuário"""
        if self.user_type == 'super_admin':
            # Super admin tem todas as permissões
            from . import Permission
            return [perm.name for perm in Permission.query.all()]
        
        return [
            user_perm.permission.name 
            for user_perm in self.user_permissions 
            if user_perm.is_active
        ]
    
    def is_super_admin(self):
        """Verifica se o usuário é super admin"""
        return self.user_type == 'super_admin'
    
    def is_admin(self):
        """Verifica se o usuário é admin ou super admin"""
        return self.user_type in ['admin', 'super_admin']
    
    def can_manage_user(self, target_user):
        """Verifica se pode gerenciar outro usuário"""
        if self.user_type == 'super_admin':
            return True
        if self.user_type == 'admin' and target_user.user_type == 'cliente':
            return True
        return False

    def to_dict(self):
        return {
            'id': str(self.id),
            'cpf': self.cpf,
            'email': self.email,
            'user_type': self.user_type,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'identity_front_path': self.identity_front_path,
            'identity_back_path': self.identity_back_path,
            'selfie_with_document_path': self.selfie_with_document_path,
            'combined_pdf_path': self.combined_pdf_path,
            'documents_uploaded_at': self.documents_uploaded_at.isoformat() if self.documents_uploaded_at else None,
            'documents_approved': self.documents_approved,
            'documents_approved_at': self.documents_approved_at.isoformat() if self.documents_approved_at else None,
            'documents_approved_by': str(self.documents_approved_by) if self.documents_approved_by else None,
            'first_access_completed': self.first_access_completed,
            'is_super_admin': self.is_super_admin(),
            'is_admin': self.is_admin(),
            'permissions': []  # Temporariamente vazio até as tabelas de permissão serem criadas
        }

class Activation(db.Model):
    __tablename__ = 'activations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    operator = db.Column(db.Enum('vivo', 'claro', 'tim', name='operator_enum'), nullable=False)
    chip_type = db.Column(db.Enum('fisico', 'esim', name='chip_type_enum'), nullable=False)
    ddd = db.Column(db.String(2), nullable=False)
    iccid = db.Column(db.String(50))
    eid = db.Column(db.String(50))
    imei = db.Column(db.String(50))
    device_type = db.Column(db.Enum('iphone', 'android', name='device_type_enum'))
    service_type = db.Column(db.Enum('pos_pago', 'pre_pago', 'controle', name='service_type_enum'))
    status = db.Column(db.Enum('pendente_contrato', 'pendente_documentos', 'pendente_dados_tecnicos', 'pendente_analise_documentos', 'documentos_rejeitados', 'em_analise', 'aprovado', 'reprovado', 'pendente_confirmacao_qr', 'ativada', 'cancelado', name='activation_status_enum'), default='pendente_contrato')
    contract_accepted = db.Column(db.Boolean, default=False)
    contract_accepted_at = db.Column(db.DateTime(timezone=True))
    contract_ip = db.Column(db.String(45))
    contract_acceptance_id = db.Column(UUID(as_uuid=True), db.ForeignKey('contract_acceptances.id'))
    documents_uploaded_at = db.Column(db.DateTime(timezone=True))
    technical_data_completed_at = db.Column(db.DateTime(timezone=True))
    approved_at = db.Column(db.DateTime(timezone=True))
    approved_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    qr_code_path = db.Column(db.String(500))
    qr_scanned_at = db.Column(db.DateTime(timezone=True))
    line_number = db.Column(db.String(20))  # Número da linha quando ativada
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    documents = db.relationship('Document', backref='activation', lazy=True)
    history = db.relationship('ActivationHistory', backref='activation', lazy=True)
    notifications = db.relationship('Notification', backref='activation', lazy=True)
    contract_acceptance = db.relationship('ContractAcceptance', foreign_keys=[contract_acceptance_id], back_populates='activations', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'operator': self.operator,
            'chip_type': self.chip_type,
            'ddd': self.ddd,
            'iccid': self.iccid,
            'eid': self.eid,
            'imei': self.imei,
            'device_type': self.device_type,
            'service_type': self.service_type,
            'status': self.status,
            'contract_accepted': self.contract_accepted,
            'contract_accepted_at': self.contract_accepted_at.isoformat() if self.contract_accepted_at else None,
            'documents_uploaded_at': self.documents_uploaded_at.isoformat() if self.documents_uploaded_at else None,
            'technical_data_completed_at': self.technical_data_completed_at.isoformat() if self.technical_data_completed_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by': str(self.approved_by) if self.approved_by else None,
            'qr_code_path': self.qr_code_path,
            'qr_scanned_at': self.qr_scanned_at.isoformat() if self.qr_scanned_at else None,
            'line_number': self.line_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user_permissions = db.relationship('UserPermission', backref='permission', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserPermission(db.Model):
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    permission_id = db.Column(db.String(36), db.ForeignKey('permissions.id'), nullable=False)
    granted_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], backref='user_permissions', lazy=True)
    granter = db.relationship('User', foreign_keys=[granted_by], lazy=True)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'permission_id'),)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'permission_id': str(self.permission_id),
            'granted_by': str(self.granted_by) if self.granted_by else None,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'is_active': self.is_active,
            'permission': self.permission.to_dict() if self.permission else None
        }

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('activations.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    document_type = db.Column(db.Enum('identity_front', 'identity_back', 'selfie_with_document', 'qr_code_esim', 'combined_contract', name='document_type_enum'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', name='document_status_enum'), default='pending')
    uploaded_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    is_approved = db.Column(db.Boolean)
    approved_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime(timezone=True))
    reviewed_at = db.Column(db.DateTime(timezone=True))
    reviewed_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    rejection_reason = db.Column(db.Text)
    
    # Relacionamento com usuário
    user = db.relationship('User', foreign_keys=[user_id], lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'activation_id': str(self.activation_id),
            'user_id': str(self.user_id),
            'document_type': self.document_type,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'status': self.status,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_approved': self.is_approved,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': str(self.reviewed_by) if self.reviewed_by else None,
            'rejection_reason': self.rejection_reason
        }

class DDD(db.Model):
    __tablename__ = 'ddds'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operator = db.Column(db.Enum('vivo', 'claro', 'tim', name='operator_enum'), nullable=False)
    ddd = db.Column(db.String(2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('operator', 'ddd'),)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'operator': self.operator,
            'ddd': self.ddd,
            'is_active': self.is_active,
            'created_by': str(self.created_by) if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ActivationHistory(db.Model):
    __tablename__ = 'activation_history'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('activations.id'), nullable=False)
    previous_status = db.Column(db.Enum('pendente_contrato', 'pendente_documentos', 'pendente_dados_tecnicos', 'pendente_analise_documentos', 'documentos_rejeitados', 'em_analise', 'aprovado', 'reprovado', 'pendente_confirmacao_qr', 'ativada', 'cancelado', name='activation_status_enum'))
    new_status = db.Column(db.Enum('pendente_contrato', 'pendente_documentos', 'pendente_dados_tecnicos', 'pendente_analise_documentos', 'documentos_rejeitados', 'em_analise', 'aprovado', 'reprovado', 'pendente_confirmacao_qr', 'ativada', 'cancelado', name='activation_status_enum'), nullable=False)
    changed_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    change_reason = db.Column(db.Text)
    changed_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'activation_id': str(self.activation_id),
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'changed_by': str(self.changed_by),
            'change_reason': self.change_reason,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None
        }

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(100))
    resource_id = db.Column(db.String(100))  # Changed to string to support UUIDs
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    activation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('activations.id'))
    type = db.Column(db.Enum('email', 'push', 'system', name='notification_type_enum'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime(timezone=True))
    read_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'activation_id': str(self.activation_id) if self.activation_id else None,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'read': self.read_at is not None,  # Frontend espera 'read' ao invés de 'is_read'
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ContractAcceptance(db.Model):
    __tablename__ = 'contract_acceptances'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    cpf = db.Column(db.String(11), nullable=False)
    security_token = db.Column(db.String(128), nullable=False, unique=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text)
    accepted_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    contract_version = db.Column(db.String(50), default='1.0')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    # Relacionamentos
    activations = db.relationship('Activation', foreign_keys='Activation.contract_acceptance_id', back_populates='contract_acceptance', lazy=True)
    
    @staticmethod
    def generate_security_token():
        """Gera um token de segurança único"""
        return secrets.token_urlsafe(64)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'cpf': self.cpf,
            'security_token': self.security_token,
            'ip_address': self.ip_address,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'contract_version': self.contract_version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PdfGenerationJob(db.Model):
    __tablename__ = 'pdf_generation_jobs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    activation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('activations.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', name='pdf_job_status_enum'), default='pending')
    progress = db.Column(db.Integer, default=0)  # 0-100
    error_message = db.Column(db.Text)
    selected_documents = db.Column(db.JSON)  # Lista de IDs dos documentos selecionados
    generated_pdf_id = db.Column(UUID(as_uuid=True), db.ForeignKey('generated_pdfs.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    started_at = db.Column(db.DateTime(timezone=True))
    completed_at = db.Column(db.DateTime(timezone=True))
    
    # Relacionamentos
    user = db.relationship('User', backref='pdf_jobs', lazy=True)
    activation = db.relationship('Activation', backref='pdf_jobs', lazy=True)
    generated_pdf = db.relationship('GeneratedPdf', back_populates='generation_job', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'activation_id': str(self.activation_id),
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'selected_documents': self.selected_documents,
            'generated_pdf_id': str(self.generated_pdf_id) if self.generated_pdf_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class GeneratedPdf(db.Model):
    __tablename__ = 'generated_pdfs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    activation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('activations.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), default='application/pdf')
    document_hash = db.Column(db.String(64))  # SHA-256 hash para verificação de integridade
    included_documents = db.Column(db.JSON)  # Metadados dos documentos incluídos
    contract_text_included = db.Column(db.Boolean, default=True)
    digital_signature_ready = db.Column(db.Boolean, default=True)
    download_count = db.Column(db.Integer, default=0)
    last_downloaded_at = db.Column(db.DateTime(timezone=True))
    expires_at = db.Column(db.DateTime(timezone=True))  # Data de expiração do arquivo
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='generated_pdfs', lazy=True)
    activation = db.relationship('Activation', backref='generated_pdfs', lazy=True)
    generation_job = db.relationship('PdfGenerationJob', back_populates='generated_pdf', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'activation_id': str(self.activation_id),
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'document_hash': self.document_hash,
            'included_documents': self.included_documents,
            'contract_text_included': self.contract_text_included,
            'digital_signature_ready': self.digital_signature_ready,
            'download_count': self.download_count,
            'last_downloaded_at': self.last_downloaded_at.isoformat() if self.last_downloaded_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

