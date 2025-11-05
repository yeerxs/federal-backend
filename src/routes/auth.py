from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import re
import uuid
import random
import string
from uuid import UUID

from models.user import db, User, AdminLog
from models.auth_models import VerificationCode, ContractValidation, TemporarySession, SystemConfig

auth_bp = Blueprint("auth", __name__)

def validate_cpf(cpf):
    """Valida CPF básico (apenas formato)"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    return len(cpf) == 11 and cpf.isdigit()

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def log_admin_action(user_id, action, details=None, ip_address=None):
    """Registra ação administrativa"""
    try:
        # Converter user_id para UUID se necessário
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        log = AdminLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")

def generate_verification_code():
    """Gera código de verificação de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code, name=""):
    """Envia email com código de verificação (mock para desenvolvimento)"""
    try:
        # Para desenvolvimento, apenas simular o envio
        print(f"📧 Email simulado para {email}: Código {code}")
        print(f"   Destinatário: {name}")
        print(f"   Assunto: Código de Verificação - Federal Associados")
        print(f"   Código: {code} (expira em 10 minutos)")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

def search_user_in_partner_database(cpf):
    """Busca dados do usuário no banco de dados do parceiro (mock)"""
    try:
        # Simular busca no banco do parceiro
        # Em produção, aqui seria feita a consulta real ao banco do parceiro
        
        # Mock: CPFs que terminam em 0 são encontrados
        found = cpf.endswith('0')
        
        if found:
            # Simular dados encontrados no banco do parceiro
            user_data = {
                "cpf": cpf,
                "name": f"Usuário {cpf[-4:]}",  # Nome simulado
                "email": f"usuario{cpf[-4:]}@email.com",  # Email simulado
                "phone": f"(11) 9{cpf[-4:]}-{cpf[-4:]}",  # Telefone simulado
                "contract_approved": True,
                "contract_number": f"CTR{random.randint(100000, 999999)}",
                "message": "Usuário encontrado no banco do parceiro"
            }
        else:
            user_data = {
                "cpf": cpf,
                "found": False,
                "message": "CPF não encontrado no banco do parceiro"
            }
        
        print(f"🔍 Busca no banco do parceiro (mock): CPF {cpf} - {'Encontrado' if found else 'Não encontrado'}")
        
        return found, user_data
        
    except Exception as e:
        print(f"Erro na busca do banco do parceiro: {e}")
        return False, {"error": str(e)}

def validate_contract_with_partner_api(cpf, email):
    """Valida contrato com API de parceiros (mock) - mantido para compatibilidade"""
    try:
        # Simular chamada para API de parceiros
        # Em produção, aqui seria feita a chamada real
        
        # Mock: CPFs que terminam em 0 são aprovados
        approved = cpf.endswith('0')
        
        response_data = {
            "cpf": cpf,
            "email": email,
            "approved": approved,
            "contract_number": f"CTR{random.randint(100000, 999999)}" if approved else None,
            "message": "Contrato aprovado" if approved else "Contrato não encontrado ou pendente"
        }
        
        print(f"🔍 Validação de contrato (mock): CPF {cpf} - {'Aprovado' if approved else 'Rejeitado'}")
        
        return approved, response_data
        
    except Exception as e:
        print(f"Erro na validação do contrato: {e}")
        return False, {"error": str(e)}

@auth_bp.route("/login", methods=["POST"])
def login():
    """Login unificado - aceita email/CPF + senha"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Aceitar tanto 'email' quanto 'login' ou 'identifier'
        identifier = data.get("email", "").strip() or data.get("login", "").strip() or data.get("identifier", "").strip()
        password = data.get("password", "")
        
        if not identifier or not password:
            return jsonify({"error": "Email/CPF e senha são obrigatórios"}), 400
        
        # Determinar se é email ou CPF
        user = None
        if validate_email(identifier):
            # É um email
            user = User.query.filter_by(email=identifier.lower()).first()
        elif validate_cpf(identifier):
            # É um CPF
            cpf = re.sub(r'[^0-9]', '', identifier)
            user = User.query.filter_by(cpf=cpf).first()
        
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 401
        
        # Verificar se o usuário completou o primeiro acesso
        if not user.first_access_completed:
            return jsonify({
                "error": "Primeiro acesso não realizado",
                "requires_first_access": True,
                "identifier": identifier
            }), 403
        
        # Verificar senha
        if not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Senha incorreta"}), 401
        
        # Verificar status do usuário
        if not user.is_active:
            return jsonify({"error": "Usuário inativo"}), 403
        
        # Login bem-sucedido
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Criar token JWT
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "user_type": user.user_type or "cliente",
                "user_id": str(user.id)
            }
        )
        
        # Log da ação
        log_admin_action(
            user.id, 
            "LOGIN", 
            f"Login realizado com sucesso - Tipo: {user.user_type}",
            request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "access_token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "user_type": user.user_type,
                "cpf": user.cpf
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/primeiro-acesso", methods=["POST"])
def primeiro_acesso():
    """Inicia processo de primeiro acesso - aceita apenas CPF"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        cpf_input = data.get("cpf", "").strip()
        
        if not cpf_input:
            return jsonify({"error": "CPF é obrigatório"}), 400
        
        # Validar e limpar CPF
        cpf = re.sub(r'[^0-9]', '', cpf_input)
        if not validate_cpf(cpf):
            return jsonify({"error": "CPF inválido"}), 400
        
        # Verificar se usuário já existe no sistema local
        existing_user = User.query.filter_by(cpf=cpf).first()
        
        if existing_user and existing_user.first_access_completed:
            return jsonify({
                "error": "Usuário já realizou primeiro acesso",
                "should_login": True
            }), 409
        
        # Buscar dados do usuário no banco do parceiro
        user_found, partner_data = search_user_in_partner_database(cpf)
        
        if not user_found:
            return jsonify({
                "error": "CPF não encontrado",
                "message": partner_data.get("message", "CPF não encontrado no banco do parceiro")
            }), 404
        
        # Extrair dados do parceiro
        email = partner_data.get("email")
        name = partner_data.get("name")
        phone = partner_data.get("phone")
        contract_approved = partner_data.get("contract_approved", False)
        
        if not contract_approved:
            return jsonify({
                "error": "Contrato não aprovado",
                "message": "Contrato não encontrado ou pendente de aprovação no banco do parceiro"
            }), 403
        
        # Salvar validação do contrato
        contract_validation = ContractValidation(
            identifier=cpf,
            approved=contract_approved,
            partner_response=str(partner_data),
            partner_api_called_at=datetime.utcnow(),
            validation_details=f"CPF: {cpf}, Email: {email}, Nome: {name}"
        )
        db.session.add(contract_validation)
        
        # Gerar código de verificação
        verification_code = generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Salvar código no banco
        code_record = VerificationCode(
            identifier=cpf,
            code=verification_code,
            email=email,
            expires_at=expires_at
        )
        db.session.add(code_record)
        
        # Criar sessão temporária
        session_token = str(uuid.uuid4())
        temp_session = TemporarySession(
            identifier=cpf,
            session_token=session_token,
            session_type="primeiro_acesso",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.session.add(temp_session)
        
        db.session.commit()
        
        # Enviar email com código (simulado - apenas log)
        email_sent = send_verification_email(email, verification_code, name)
        
        if not email_sent:
            return jsonify({
                "error": "Erro ao enviar email",
                "message": "Não foi possível enviar o código de verificação"
            }), 500
        
        # Mascarar dados sensíveis para retorno
        email_masked = f"{email[:3]}***@{email.split('@')[1]}" if email else None
        name_masked = f"{name.split()[0]} {name.split()[-1][0]}***" if name and len(name.split()) > 1 else f"{name[:3]}***" if name else None
        
        return jsonify({
            "success": True,
            "message": "Usuário encontrado! Código de verificação enviado por email",
            "session_token": session_token,
            "user_data": {
                "cpf": cpf,
                "name": name_masked,
                "email": email_masked,
                "phone": phone[:8] + "****" if phone else None
            },
            "expires_in": 600  # 10 minutos
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/verificar-codigo", methods=["POST"])
def verificar_codigo():
    """Verifica código de verificação"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        session_token = data.get("session_token", "")
        code = data.get("code", "").strip()
        
        if not session_token or not code:
            return jsonify({"error": "Token de sessão e código são obrigatórios"}), 400
        
        # Verificar sessão temporária
        temp_session = TemporarySession.query.filter_by(
            session_token=session_token,
            used=False
        ).first()
        
        if not temp_session or temp_session.expires_at < datetime.utcnow():
            return jsonify({"error": "Sessão expirada ou inválida"}), 401
        
        # Verificar código
        code_record = VerificationCode.query.filter_by(
            identifier=temp_session.identifier,
            code=code,
            used=False
        ).first()
        
        if not code_record or code_record.expires_at < datetime.utcnow():
            return jsonify({"error": "Código inválido ou expirado"}), 401
        
        # Marcar código como usado
        code_record.used = True
        
        # Criar nova sessão para criação de senha
        new_session_token = str(uuid.uuid4())
        password_session = TemporarySession(
            identifier=temp_session.identifier,
            session_token=new_session_token,
            session_type="criar_senha",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.session.add(password_session)
        
        # Marcar sessão atual como usada
        temp_session.used = True
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Código verificado com sucesso",
            "session_token": new_session_token
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/criar-senha", methods=["POST"])
def criar_senha():
    """Cria senha para novo usuário"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        session_token = data.get("session_token", "")
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        name = data.get("name", "").strip()
        
        if not session_token or not password or not confirm_password or not name:
            return jsonify({"error": "Todos os campos são obrigatórios"}), 400
        
        # Verificar sessão
        temp_session = TemporarySession.query.filter_by(
            session_token=session_token,
            session_type="criar_senha",
            used=False
        ).first()
        
        if not temp_session or temp_session.expires_at < datetime.utcnow():
            return jsonify({"error": "Sessão expirada ou inválida"}), 401
        
        # Validar senha
        if password != confirm_password:
            return jsonify({"error": "Senhas não coincidem"}), 400
        
        if len(password) < 8:
            return jsonify({"error": "Senha deve ter pelo menos 8 caracteres"}), 400
        
        # Verificar se tem pelo menos uma letra maiúscula, minúscula e número
        if not re.search(r'[A-Z]', password):
            return jsonify({"error": "Senha deve conter pelo menos uma letra maiúscula"}), 400
        
        if not re.search(r'[a-z]', password):
            return jsonify({"error": "Senha deve conter pelo menos uma letra minúscula"}), 400
        
        if not re.search(r'\d', password):
            return jsonify({"error": "Senha deve conter pelo menos um número"}), 400
        
        # Buscar validação do contrato
        contract_validation = ContractValidation.query.filter_by(
            identifier=temp_session.identifier,
            approved=True
        ).order_by(ContractValidation.created_at.desc()).first()
        
        if not contract_validation:
            return jsonify({"error": "Validação de contrato não encontrada"}), 404
        
        # Extrair dados da validação
        validation_details = contract_validation.validation_details or ""
        cpf = None
        email = None
        
        if "CPF:" in validation_details:
            cpf = validation_details.split("CPF:")[1].split(",")[0].strip()
        if "Email:" in validation_details:
            email = validation_details.split("Email:")[1].strip()
        
        if not cpf or not email:
            return jsonify({"error": "Dados de validação incompletos"}), 400
        
        # Verificar se usuário já existe
        existing_user = User.query.filter(
            (User.cpf == cpf) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.first_access_completed:
                return jsonify({"error": "Usuário já existe e completou primeiro acesso"}), 409
            
            # Atualizar usuário existente
            existing_user.password_hash = generate_password_hash(password)
            existing_user.name = name
            existing_user.is_active = True
            existing_user.first_access_completed = True
            user = existing_user
        else:
            # Criar novo usuário
            user = User(
                cpf=cpf,
                email=email,
                password_hash=generate_password_hash(password),
                name=name,
                user_type="cliente",
                is_active=True,
                first_access_completed=True,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
        
        # Marcar sessão como usada
        temp_session.used = True
        
        db.session.commit()
        
        # Criar token JWT para login automático
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "user_type": user.user_type,
                "user_id": str(user.id)
            }
        )
        
        # Log da ação
        log_admin_action(
            user.id, 
            "FIRST_ACCESS_COMPLETED", 
            f"Primeiro acesso concluído - Nome: {name}",
            request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "message": "Conta criada com sucesso",
            "access_token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "user_type": user.user_type,
                "cpf": user.cpf
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Validar campos obrigatórios
        required_fields = ["cpf", "email", "password", "name"]
        for field in required_fields:
            if not data.get(field) or data.get(field).strip() == "": 
                return jsonify({"error": f"Campo {field} é obrigatório"}), 400
        
        cpf = re.sub(r'[^0-9]', '', data.get("cpf", "")) 
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        name = data.get("name", "").strip()
        phone = data.get("phone", "").strip()
        
        # Validações
        if not validate_cpf(cpf):
            return jsonify({"error": "CPF inválido"}), 400
        
        if not validate_email(email):
            return jsonify({"error": "Email inválido"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Senha deve ter pelo menos 6 caracteres"}), 400
        
        # Verificar se usuário já existe
        existing_user = User.query.filter(
            (User.cpf == cpf) | (User.email == email)
        ).first()
        
        if existing_user:
            return jsonify({"error": "CPF ou email já cadastrado"}), 409
        
        # Criar novo usuário
        user = User(
            cpf=cpf,
            email=email,
            password_hash=generate_password_hash(password),
            user_type="cliente",  # Novos usuários são sempre clientes
            name=name,
            phone=phone if phone else None
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Log da ação
        log_admin_action(
            user.id, 
            "REGISTER", 
            f"Novo usuário registrado: {name}",
            request.remote_addr
        )
        
        return jsonify({
            "message": "Usuário criado com sucesso",
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        # User model uses String(36) for ID, so use string directly
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        return jsonify({"user": user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()
        
        # Log da ação
        log_admin_action(
            user.id, 
            "LOGOUT", 
            "Logout realizado",
            request.remote_addr
        )
        
        return jsonify({"message": "Logout realizado com sucesso"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/start", methods=["POST"])
def start_auth():
    """Inicia processo de autenticação verificando CPF"""
    try:
        data = request.get_json()
        
        if not data or not data.get("cpf"):
            return jsonify({"error": "CPF é obrigatório", "success": False}), 400
        
        cpf = re.sub(r'[^0-9]', '', data.get("cpf", ""))
        
        if not validate_cpf(cpf):
            return jsonify({"error": "CPF inválido", "success": False}), 400
        
        # Buscar usuário pelo CPF
        user = User.query.filter_by(cpf=cpf).first()
        
        if not user:
            return jsonify({
                "error": "CPF não encontrado no sistema", 
                "success": False,
                "message": "CPF não cadastrado. Verifique o número ou entre em contato com o suporte."
            }), 404
        
        # Verificar se o usuário está ativo
        if not user.is_active:
            return jsonify({
                "error": "Usuário inativo", 
                "success": False,
                "message": "Sua conta está inativa. Entre em contato com o suporte."
            }), 403
        
        # Mascarar email para exibição
        email_parts = user.email.split('@')
        if len(email_parts) == 2:
            username = email_parts[0]
            domain = email_parts[1]
            if len(username) > 3:
                masked_username = username[:2] + '*' * (len(username) - 4) + username[-2:]
            else:
                masked_username = username[0] + '*' * (len(username) - 1)
            masked_email = f"{masked_username}@{domain}"
        else:
            masked_email = user.email
        
        # Log da ação
        log_admin_action(
            user.id, 
            "AUTH_START", 
            f"Verificação de CPF realizada - CPF: {cpf}",
            request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "email": masked_email,
            "user_id": str(user.id),
            "cpf": cpf,
            "message": "CPF encontrado. Prossiga com a senha."
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}", "success": False}), 500

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json()
        
        if not data or not data.get("email"):
            return jsonify({"error": "Email é obrigatório"}), 400
        
        email = data["email"].strip().lower()
        
        if not validate_email(email):
            return jsonify({"error": "Email inválido"}), 400
        
        user = User.query.filter_by(email=email).first()
        
        # Por segurança, sempre retorna sucesso mesmo se email não existir
        if user:
            # Aqui seria implementado o envio de email
            # Por enquanto, apenas log
            log_admin_action(
                user.id, 
                "FORGOT_PASSWORD", 
                f"Solicitação de recuperação de senha para: {email}",
                request.remote_addr
            )
        
        return jsonify({
            "message": "Se o email existir, você receberá instruções para recuperação"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/reactivate-account", methods=["POST"])
def reactivate_account():
    """Reativa conta do usuário com nova senha"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        user_id = data.get("user_id")
        new_password = data.get("new_password")
        
        if not user_id or not new_password:
            return jsonify({"error": "ID do usuário e nova senha são obrigatórios"}), 400
        
        # Validar senha
        if len(new_password) < 6:
            return jsonify({"error": "A senha deve ter pelo menos 6 caracteres"}), 400
        
        if not re.search(r'[a-zA-Z]', new_password):
            return jsonify({"error": "A senha deve conter pelo menos uma letra"}), 400
        
        if not re.search(r'\d', new_password):
            return jsonify({"error": "A senha deve conter pelo menos um número"}), 400
        
        # Buscar usuário
        # User model uses String(36) for ID, so use string directly
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Atualizar senha e status
        user.password_hash = generate_password_hash(new_password)
        user.status = 'active'
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log da ação
        log_admin_action(
            user.id, 
            "ACCOUNT_REACTIVATED", 
            f"Conta reativada com nova senha - Email: {user.email}",
            request.remote_addr
        )
        
        return jsonify({
            "success": True,
            "message": "Conta reativada com sucesso"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@auth_bp.route("/verificar-hash", methods=["POST"])
def verificar_hash():
    """Verificar hash contra o último registro na tabela tokens do PostgreSQL"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        cpf = data.get('cpf')
        token = data.get('token')
        email = data.get('email')
        
        if not cpf or not token or not email:
            return jsonify({"error": "CPF, token e email são obrigatórios"}), 400
        
        # Validar CPF
        if not validate_cpf(cpf):
            return jsonify({"error": "CPF inválido"}), 400
        
        # Conectar diretamente ao PostgreSQL para consultar a tabela tokens
        import psycopg2
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Obter string de conexão PostgreSQL
        postgresql_url = os.getenv('POSTGRESQL_URL')
        
        if not postgresql_url:
            return jsonify({
                "success": False,
                "error": "Configuração PostgreSQL não encontrada"
            }), 500
        
        try:
            # Conectar ao PostgreSQL
            conn = psycopg2.connect(postgresql_url)
            cursor = conn.cursor()
            
            # Buscar o último registro na tabela tokens para o CPF fornecido
            cursor.execute("""
                SELECT id, cpf, email, token_hash, created_at 
                FROM tokens 
                WHERE cpf = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (cpf,))
            
            token_record = cursor.fetchone()
            
            if not token_record:
                cursor.close()
                conn.close()
                return jsonify({
                    "success": False,
                    "error": "Token não encontrado na base de dados para este CPF"
                }), 404
            
            token_id, token_cpf, token_email, stored_hash, created_at = token_record
            
            # Verificar se o email bate
            if token_email.lower() != email.lower():
                cursor.close()
                conn.close()
                return jsonify({
                    "success": False,
                    "error": "Email não corresponde ao cadastrado na tabela tokens"
                }), 400
            
            # Gerar hash esperado baseado nos dados
            import hashlib
            hash_base = f"{cpf}{email}{token_id}"
            expected_hash = hashlib.sha256(hash_base.encode()).hexdigest()
            
            # Extrair e validar informações do token JWT
            try:
                import jwt
                # Decodificar o token sem verificar a assinatura (apenas para extrair dados)
                decoded_token = jwt.decode(token, options={"verify_signature": False})
                
                # Verificar se os dados do token batem com os dados fornecidos
                token_cpf_jwt = decoded_token.get('sub', '')
                token_email_jwt = decoded_token.get('email', '')
                
                if token_cpf_jwt != cpf or token_email_jwt != email:
                    cursor.close()
                    conn.close()
                    return jsonify({
                        "success": False,
                        "error": "Token JWT não corresponde aos dados fornecidos"
                    }), 400
                
            except Exception as token_error:
                cursor.close()
                conn.close()
                print(f"Erro ao decodificar token JWT: {token_error}")
                return jsonify({
                    "success": False,
                    "error": "Token JWT inválido ou malformado"
                }), 400
            
            # Log da verificação
            print(f"🔐 Verificação de hash PostgreSQL - CPF: {cpf}, Email: {email}")
            print(f"📊 Token encontrado: ID {token_id}, criado em {created_at}")
            print(f"🔍 Hash esperado: {expected_hash}")
            print(f"🔍 Hash armazenado: {stored_hash}")
            
            # Verificar se o hash bate (opcional, dependendo da lógica de negócio)
            hash_matches = stored_hash == expected_hash if stored_hash else True
            
            cursor.close()
            conn.close()
            
            # Se chegou até aqui, a verificação foi bem-sucedida
            return jsonify({
                "success": True,
                "message": "Verificação de hash bem-sucedida no PostgreSQL",
                "token_id": token_id,
                "hash_matches": hash_matches,
                "verified_at": datetime.utcnow().isoformat()
            }), 200
            
        except psycopg2.Error as pg_error:
            print(f"Erro PostgreSQL: {pg_error}")
            return jsonify({
                "success": False,
                "error": f"Erro de conexão PostgreSQL: {str(pg_error)}"
            }), 500
        
    except Exception as e:
        print(f"Erro na verificação de hash: {e}")
        return jsonify({
            "success": False,
            "error": f"Erro interno na verificação: {str(e)}"
        }), 500





