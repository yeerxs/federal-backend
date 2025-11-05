from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import shutil
import uuid
from uuid import UUID
import qrcode
from io import BytesIO

from models.user import db, User, Activation, Document, DDD, ActivationHistory, Notification, ContractAcceptance
from utils.pdf_generator import create_combined_pdf

client_bp = Blueprint("client", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def require_client():
    """Decorator para verificar se usuário é cliente ou admin"""
    claims = get_jwt()
    if claims.get("user_type") not in ["cliente", "admin"]:
        return jsonify({"error": "Acesso negado"}), 403
    return None

def log_activation_change(activation_id, previous_status, new_status, user_id, reason=None):
    """Registra mudança de status da ativação"""
    try:
        # Converter IDs para UUID se necessário
        if isinstance(activation_id, str):
            activation_id = UUID(activation_id)
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        
        history = ActivationHistory(
            activation_id=activation_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=user_id,
            change_reason=reason
        )
        db.session.add(history)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar histórico: {e}")

def create_notification(user_id, title, message, activation_id=None):
    """Cria notificação para o usuário"""
    try:
        # Converter IDs para UUID se necessário
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        if activation_id and isinstance(activation_id, str):
            activation_id = UUID(activation_id)
        
        notification = Notification(
            user_id=user_id,
            activation_id=activation_id,
            type="system",
            title=title,
            message=message
        )
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")

@client_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        # User model uses String(36) for ID, so use string directly
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # For other models that use UUID, convert user_id to UUID
        user_uuid = UUID(user_id)
        # Buscar ativações do usuário
        activations = Activation.query.filter_by(user_id=user_uuid).order_by(Activation.created_at.desc()).all()
        
        # Permitir criação ilimitada de ativações para testes
        can_create_new = True
        
        # Buscar notificações não lidas
        unread_notifications = Notification.query.filter(
            Notification.user_id == user_uuid,
            Notification.read_at.is_(None)
        ).order_by(Notification.created_at.desc()).all()
        
        return jsonify({
            "user": user.to_dict(),
            "activations": [activation.to_dict() for activation in activations],
            "can_create_new_activation": can_create_new,
            "unread_notifications": [notif.to_dict() for notif in unread_notifications]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/activations/contract-only", methods=["POST"])
@jwt_required()
def create_activation_contract_only():
    """Cria ativação apenas com dados básicos, sem documentos"""
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        
        # Verificar limite de 2 ativações por CPF
        # User model uses String(36) for ID, so use string directly
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # For other models that use UUID, convert user_id to UUID
        user_uuid = UUID(user_id)
        # Contar ativações existentes do usuário (excluindo canceladas)
        existing_activations = Activation.query.filter(
            Activation.user_id == user_uuid,
            Activation.status != 'cancelado'
        ).count()
        
        if existing_activations >= 2:
            return jsonify({
                "error": "Limite de 2 ativações por CPF atingido. Entre em contato com o suporte para mais informações."
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Receber dados básicos
        operator = data.get("operator")
        chip_type = data.get("chip_type")
        ddd = data.get("ddd")
        
        # Validar campos obrigatórios básicos
        required_fields = ["operator", "chip_type", "ddd"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo {field} é obrigatório"}), 400
        
        # Validar operadora
        if operator not in ["vivo", "claro", "tim"]:
            return jsonify({"error": "Operadora inválida"}), 400
        
        # Validar tipo de chip
        if chip_type not in ["esim", "fisico"]:
            return jsonify({"error": "Tipo de chip inválido"}), 400
        
        # Verificar se DDD está disponível para a operadora
        ddd_available = DDD.query.filter_by(
            operator=operator, 
            ddd=ddd, 
            is_active=True
        ).first()
        
        if not ddd_available:
            return jsonify({"error": "DDD não disponível para esta operadora"}), 400
        
        # Criar nova ativação com status pendente_contrato
        activation = Activation(
            user_id=user_uuid,
            operator=operator,
            chip_type=chip_type,
            ddd=ddd,
            status="pendente_contrato",
            contract_accepted=False
        )
        
        db.session.add(activation)
        db.session.commit()
        
        # Registrar histórico
        log_activation_change(
            activation.id, 
            None, 
            "pendente_contrato", 
            user_id, 
            "Ativação criada - aguardando aceite do contrato"
        )
        
        # Criar notificação
        create_notification(
            user_id,
            "Ativação Criada",
            "Sua ativação foi criada. Aceite o contrato para continuar.",
            activation.id
        )
        
        return jsonify({
            "message": "Ativação criada com sucesso",
            "activation": activation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/activations", methods=["POST"])
@jwt_required()
def create_activation():
    """Criar nova ativação - apenas dados básicos, sem documentos"""
    try:
        print(f"[DEBUG] Iniciando criação de ativação")
        
        auth_check = require_client()
        if auth_check:
            print(f"[DEBUG] Falha na verificação de autorização")
            return auth_check
        
        user_id = get_jwt_identity()
        print(f"[DEBUG] User ID: {user_id}")
        
        # User model uses String(36) for ID, so use string directly
        user = User.query.get(user_id)
        
        if not user:
            print(f"[DEBUG] Usuário não encontrado: {user_id}")
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        print(f"[DEBUG] Usuário encontrado: {user.name}")
        
        # For other models that use UUID, convert user_id to UUID
        user_uuid = UUID(user_id)
        # Verificar limite de ativações por CPF
        existing_activations = Activation.query.filter(
            Activation.user_id == user_uuid,
            Activation.status != 'cancelado'
        ).count()
        
        print(f"[DEBUG] Ativações existentes: {existing_activations}")
        
        if existing_activations >= 2:
            print(f"[DEBUG] Limite de ativações atingido")
            return jsonify({
                "error": "Limite de 2 ativações por CPF atingido. Entre em contato com o suporte para mais informações."
            }), 400
        
        # Obter dados do JSON (não mais FormData)
        data = request.get_json()
        print(f"[DEBUG] Dados recebidos: {data}")
        
        if not data:
            print(f"[DEBUG] Nenhum dado fornecido")
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Dados básicos obrigatórios
        operator = data.get("operator")
        chip_type = data.get("chip_type")
        ddd = data.get("ddd")
        contract_accepted = data.get("contract_accepted", False)
        
        print(f"[DEBUG] Campos: operator={operator}, chip_type={chip_type}, ddd={ddd}, contract_accepted={contract_accepted}")
        
        # Validar campos obrigatórios
        if not all([operator, chip_type, ddd]):
            print(f"[DEBUG] Campos obrigatórios faltando")
            return jsonify({"error": "Operadora, tipo de chip e DDD são obrigatórios"}), 400
        
        if not contract_accepted:
            print(f"[DEBUG] Contrato não aceito")
            return jsonify({"error": "Aceite do contrato é obrigatório"}), 400
        
        # Dados técnicos
        iccid = data.get("iccid", "")
        eid = data.get("eid", "")
        imei = data.get("imei", "")
        device_type = data.get("device_type", "")
        service_type = data.get("service_type", "")
        
        # Validação específica para Vivo eSIM
        if operator == "vivo" and chip_type == "esim":
            if not all([eid, imei, device_type]):
                return jsonify({"error": "Para ativação Vivo eSIM, EID, IMEI e tipo de dispositivo são obrigatórios"}), 400
        
        # Validação específica para chip físico (todas operadoras)
        if chip_type == "fisico":
            if not iccid:
                return jsonify({"error": "Para chip físico, o ICCID é obrigatório"}), 400
        
        # Verificar se o DDD está disponível para a operadora
        ddd_available = DDD.query.filter_by(
            operator=operator,
            ddd=ddd,
            is_active=True
        ).first()
        
        if not ddd_available:
            return jsonify({"error": "DDD não disponível para esta operadora"}), 400
        
        # Verificar se é primeira ativação (precisa de documentos)
        is_first_activation = existing_activations == 0
        
        # Determinar status inicial
        if is_first_activation:
            # Primeira ativação: precisa de documentos
            initial_status = "pendente_documentos"
        else:
            # Ativação subsequente: vai direto para análise
            initial_status = "pendente_analise_documentos"
        
        # Criar ativação
        activation = Activation(
            user_id=user_uuid,
            operator=operator,
            chip_type=chip_type,
            ddd=ddd,
            iccid=iccid if iccid else None,
            eid=eid if eid else None,
            imei=imei if imei else None,
            device_type=device_type if device_type else None,
            service_type=service_type if service_type else None,
            status=initial_status,
            contract_accepted=contract_accepted,
            contract_accepted_at=datetime.utcnow(),
            contract_ip=request.remote_addr
        )
        
        db.session.add(activation)
        db.session.commit()
        
        # Registrar histórico
        log_activation_change(
            activation.id, 
            None, 
            initial_status, 
            user_id, 
            f"Ativação criada - {'primeira ativação' if is_first_activation else 'ativação subsequente'}"
        )
        
        # Criar notificação
        if is_first_activation:
            create_notification(
                user_id,
                "Ativação Criada",
                "Sua ativação foi criada. Agora envie seus documentos para análise.",
                activation.id
            )
        else:
            create_notification(
                user_id,
                "Ativação Criada",
                "Sua ativação foi criada e está em análise.",
                activation.id
            )
        
        return jsonify({
            "message": "Ativação criada com sucesso",
            "activation": activation.to_dict(),
            "requires_documents": is_first_activation
        }), 201
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/check-contract-status/<cpf>", methods=["GET"])
@jwt_required()
def check_contract_status(cpf):
    """Verifica se o CPF já possui aceite de contrato válido"""
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        # Verificar se existe aceite de contrato ativo para este CPF
        contract_acceptance = ContractAcceptance.query.filter_by(
            cpf=cpf,
            is_active=True
        ).first()
        
        if contract_acceptance:
            return jsonify({
                "has_contract": True,
                "contract_acceptance_id": str(contract_acceptance.id),
                "accepted_at": contract_acceptance.accepted_at.isoformat(),
                "contract_version": contract_acceptance.contract_version
            }), 200
        else:
            return jsonify({
                "has_contract": False
            }), 200
            
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/activations/<activation_id>/contract", methods=["POST"])
@jwt_required()
def accept_contract(activation_id):
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        try:
            activation_uuid = UUID(activation_id)
            user_uuid = UUID(user_id)
            activation = Activation.query.filter_by(
                id=activation_uuid, 
                user_id=user_uuid
            ).first()
        except ValueError:
            return jsonify({"error": "ID inválido"}), 400

        if not activation:
            return jsonify({"error": "Ativação não encontrada"}), 404

        # Verificar se o contrato já foi aceito
        if activation.contract_accepted:
            return jsonify({"error": "Contrato já foi aceito"}), 400

        # Buscar usuário para obter CPF - User model uses String(36) for ID
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Verificar se já existe aceite de contrato para este CPF
        existing_contract = ContractAcceptance.query.filter_by(
            cpf=user.cpf,
            is_active=True
        ).first()
        
        contract_acceptance = None
        
        if existing_contract:
            # Usar aceite existente
            contract_acceptance = existing_contract
        else:
            # Criar novo aceite de contrato
            contract_acceptance = ContractAcceptance(
                user_id=user_uuid,
                cpf=user.cpf,
                security_token=ContractAcceptance.generate_security_token(),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                contract_version=data.get('contract_version', '1.0')
            )
            db.session.add(contract_acceptance)
            db.session.flush()  # Para obter o ID
        
        # Aceitar contrato na ativação
        previous_status = activation.status
        activation.contract_accepted = True
        activation.contract_accepted_at = datetime.utcnow()
        activation.contract_ip = request.remote_addr
        activation.contract_acceptance_id = contract_acceptance.id
        
        # Se estava pendente_contrato, muda para pendente_documentos
        if activation.status == "pendente_contrato":
            activation.status = "pendente_documentos"
        
        # Registrar histórico
        log_activation_change(
            activation.id, 
            previous_status, 
            activation.status, 
            user_id, 
            "Contrato aceito pelo cliente"
        )
        
        db.session.commit()
        
        # Criar notificação
        create_notification(
            user_id,
            "Contrato Aceito",
            "Contrato aceito com sucesso. Agora você pode enviar os documentos.",
            activation.id
        )
        
        return jsonify({
            "message": "Contrato aceito com sucesso",
            "activation": activation.to_dict(),
            "contract_acceptance": {
                "id": str(contract_acceptance.id),
                "security_token": contract_acceptance.security_token,
                "accepted_at": contract_acceptance.accepted_at.isoformat(),
                "is_new_acceptance": existing_contract is None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/activations/<activation_id>/documents", methods=["POST"])
@jwt_required()
def upload_documents(activation_id):
    """Upload de documentos para uma ativação existente"""
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        
        try:
            activation_uuid = UUID(activation_id)
            user_uuid = UUID(user_id)
            activation = Activation.query.filter_by(
                id=activation_uuid,
                user_id=user_uuid
            ).first()
        except ValueError:
            return jsonify({"error": "ID inválido"}), 400
        
        if not activation:
            return jsonify({"error": "Ativação não encontrada"}), 404
        
        # Verificar se está no status correto para upload de documentos
        if activation.status not in ["pendente_documentos", "documentos_rejeitados"]:
            return jsonify({"error": "Ativação não está aguardando documentos"}), 400
        
        # Verificar se já existem documentos (permitir reenvio se rejeitados)
        existing_docs = Document.query.filter_by(activation_id=activation_uuid).first()
        if existing_docs and activation.status != "documentos_rejeitados":
            return jsonify({"error": "Documentos já foram enviados para esta ativação"}), 400
        
        # Receber arquivos
        selfie_with_document = request.files.get("selfie_with_document")
        identity_front = request.files.get("identity_front")
        identity_back = request.files.get("identity_back")
        
        # Validar arquivos de documentos
        if not selfie_with_document or not identity_front or not identity_back:
            return jsonify({"error": "Todos os documentos (selfie, frente e verso do documento) são obrigatórios"}), 400
        
        files = {
            "selfie_with_document": selfie_with_document,
            "identity_front": identity_front,
            "identity_back": identity_back
        }
        
        for doc_type, file in files.items():
            if file.filename == "":
                return jsonify({"error": f"Arquivo {doc_type} não selecionado"}), 400
            if not allowed_file(file.filename):
                return jsonify({"error": f"Tipo de arquivo inválido para {doc_type}"}), 400
        
        # Salvar arquivos e criar registros no banco
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "/tmp/uploads")
        os.makedirs(upload_folder, exist_ok=True)
        saved_documents = []
        
        # Criar diretório para documentos do perfil se não existir
        profile_docs_dir = os.path.join(upload_folder, 'profile_documents', str(user_uuid))
        os.makedirs(profile_docs_dir, exist_ok=True)
        
        # Se há documentos existentes (reenvio), removê-los primeiro
        if existing_docs:
            old_documents = Document.query.filter_by(activation_id=activation_uuid).all()
            for doc in old_documents:
                try:
                    if os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                except:
                    pass
                db.session.delete(doc)
        
        # Buscar o usuário para atualizar o perfil - User model uses String(36) for ID
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        try:
            profile_files = {}
            for doc_type, file in files.items():
                file_extension = file.filename.rsplit(".", 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}_{doc_type}.{file_extension}"
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                # Salvar documento para a ativação
                document = Document(
                    activation_id=activation.id,
                    user_id=user_uuid,  # Adicionar user_id obrigatório
                    document_type=doc_type,
                    file_path=file_path,
                    file_name=file.filename,
                    file_size=os.path.getsize(file_path),
                    mime_type=file.content_type or "application/octet-stream"
                )
                db.session.add(document)
                saved_documents.append(document)
                
                # Também salvar uma cópia no perfil do cliente
                profile_filename = secure_filename(f"{doc_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                profile_file_path = os.path.join(profile_docs_dir, profile_filename)
                
                # Copiar arquivo para o diretório do perfil
                shutil.copy2(file_path, profile_file_path)
                profile_files[doc_type] = profile_file_path
            
            # Atualizar perfil do usuário com os documentos
            user.identity_front_path = profile_files.get('identity_front')
            user.identity_back_path = profile_files.get('identity_back')
            user.selfie_with_document_path = profile_files.get('selfie_with_document')
            user.documents_uploaded_at = datetime.utcnow()
            user.documents_approved = False  # Resetar aprovação
            user.documents_approved_at = None
            user.documents_approved_by = None
            
            # Gerar PDF combinado com os documentos
            print(f"🔧 Iniciando geração do PDF combinado...")
            print(f"Arquivos disponíveis: {profile_files}")
            try:
                # PDF generator já importado no topo do arquivo
                
                # Verificar se todos os arquivos existem
                selfie_path = profile_files.get('selfie_with_document')
                identity_front_path = profile_files.get('identity_front')
                identity_back_path = profile_files.get('identity_back')
                
                print(f"Selfie: {selfie_path} - Existe: {os.path.exists(selfie_path) if selfie_path else False}")
                print(f"RG Frente: {identity_front_path} - Existe: {os.path.exists(identity_front_path) if identity_front_path else False}")
                print(f"RG Verso: {identity_back_path} - Existe: {os.path.exists(identity_back_path) if identity_back_path else False}")
                
                if not all([selfie_path, identity_front_path, identity_back_path]):
                    raise Exception("Nem todos os caminhos dos documentos estão disponíveis")
                
                if not all([os.path.exists(selfie_path), os.path.exists(identity_front_path), os.path.exists(identity_back_path)]):
                    raise Exception("Nem todos os arquivos de documentos existem no sistema")
                
                pdf_path = create_combined_pdf(
                    selfie_path=selfie_path,
                    identity_front_path=identity_front_path,
                    identity_back_path=identity_back_path,
                    user_name=user.name,
                    user_cpf=user.cpf,
                    output_dir=os.path.join(upload_folder, 'combined_pdfs')
                )
                
                print(f"✅ PDF combinado criado em: {pdf_path}")
                
                # Verificar se o arquivo foi realmente criado
                if not os.path.exists(pdf_path):
                    raise Exception(f"PDF combinado não foi criado: {pdf_path}")
                
                # Salvar caminho do PDF combinado no perfil do usuário
                user.combined_pdf_path = pdf_path
                print(f"✅ Caminho do PDF salvo no perfil do usuário")
                
                # Criar registro do documento PDF combinado na tabela documents
                combined_document = Document(
                    activation_id=activation.id,
                    user_id=user_uuid,
                    document_type='combined_contract',
                    file_path=pdf_path,
                    file_name=os.path.basename(pdf_path),
                    file_size=os.path.getsize(pdf_path),
                    mime_type='application/pdf',
                    status='pending'
                )
                db.session.add(combined_document)
                saved_documents.append(combined_document)
                
                print(f"✅ PDF combinado registrado na base de dados: {os.path.basename(pdf_path)}")
                
            except Exception as pdf_error:
                print(f"❌ ERRO ao gerar PDF combinado: {str(pdf_error)}")
                # Não falhar o upload por causa do PDF, apenas logar o erro
            
            # Atualizar status da ativação
            previous_status = activation.status
            activation.status = "pendente_analise_documentos"
            
            db.session.commit()
            
            # Registrar histórico
            action_description = "Documentos reenviados pelo cliente" if existing_docs else "Documentos enviados pelo cliente"
            log_activation_change(
                activation.id, 
                previous_status, 
                "pendente_analise_documentos", 
                user_id, 
                action_description
            )
            
            # Criar notificação
            notification_message = "Documentos reenviados com sucesso. Aguarde a análise." if existing_docs else "Documentos enviados com sucesso. Aguarde a análise."
            create_notification(
                user_id,
                "Documentos Enviados",
                notification_message,
                activation.id
            )
            
            return jsonify({
                "message": "Documentos enviados com sucesso",
                "activation": activation.to_dict()
            }), 200
            
        except Exception as e:
            # Limpar arquivos salvos em caso de erro
            for doc in saved_documents:
                try:
                    if os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                except:
                    pass
            raise e
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/activations/<activation_id>/technical-data", methods=["POST"])
@jwt_required()
def complete_technical_data(activation_id):
    try:
    
        print(f"Activation ID: {activation_id}")
        
        auth_check = require_client()
        if auth_check:
            print(f"❌ Auth check failed: {auth_check}")
            return auth_check
        
        user_id = get_jwt_identity()
        print(f"User ID: {user_id}")
        
        try:
            activation_uuid = UUID(activation_id)
            user_uuid = UUID(user_id)
            activation = Activation.query.filter_by(
                id=activation_uuid, 
                user_id=user_uuid
            ).first()
        except ValueError:
            print(f"❌ Invalid UUID format")
            return jsonify({"error": "ID inválido"}), 400
        
        if not activation:
            print(f"❌ Activation not found for user {user_id}")
            return jsonify({"error": "Ativação não encontrada"}), 404
        
        print(f"✅ Activation found: {str(activation.id)}, Status: {activation.status}")
        print(f"Chip type: {activation.chip_type}, Operator: {activation.operator}")
        
        # O status agora deve ser pendente_analise_documentos ou em_analise (se admin já aprovou docs)
        if activation.status not in ["pendente_analise_documentos", "em_analise"]:
            print(f"❌ Invalid status for technical data: {activation.status}")
            return jsonify({"error": "Ativação não está no status correto para completar dados técnicos"}), 400
        
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data:
            print(f"❌ No data provided")
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Validar campos técnicos baseados na operadora e tipo
        iccid = data.get("iccid", "")
        eid = data.get("eid", "")
        imei = data.get("imei", "")
        service_type = data.get("service_type", "")
        
        print(f"Extracted fields - ICCID: '{iccid}', EID: '{eid}', IMEI: '{imei}', Service Type: '{service_type}'")
        
        # Aplicar validações específicas
        if activation.chip_type == "esim" and activation.operator == "vivo":
            print(f"Validating eSIM Vivo requirements...")
            # eSIM Vivo: EID, IMEI obrigatórios
            if not eid:
                print(f"❌ EID validation failed for eSIM Vivo")
                return jsonify({"error": "EID é obrigatório para eSIM Vivo"}), 400
            if not imei:
                print(f"❌ IMEI validation failed for eSIM Vivo")
                return jsonify({"error": "IMEI é obrigatório para eSIM Vivo"}), 400
        elif activation.chip_type == "fisico":
            print(f"Validating physical chip requirements...")
            # Chip físico: ICCID obrigatório para todas operadoras
            if not iccid:
                print(f"❌ ICCID validation failed for physical chip")
                return jsonify({"error": "ICCID é obrigatório para chip físico"}), 400
            
            # Chip Físico Vivo: service_type também obrigatório
            if activation.operator == "vivo":
                if not service_type or service_type not in ["com_voz", "somente_dados"]:
                    print(f"❌ Service type validation failed for Vivo physical chip")
                    return jsonify({"error": "Tipo de serviço é obrigatório para Chip Físico Vivo (com_voz ou somente_dados)"}), 400
        
        print(f"✅ All validations passed")
        
        # Dados antes da atualização
        print(f"Before update - ICCID: {activation.iccid}, EID: {activation.eid}, IMEI: {activation.imei}, Service Type: {activation.service_type}")
        
        # Atualizar dados técnicos da ativação
        activation.iccid = iccid if iccid else None
        activation.eid = eid if eid else None
        activation.imei = imei if imei else None
        activation.service_type = service_type if service_type else None
        
        print(f"After update - ICCID: {activation.iccid}, EID: {activation.eid}, IMEI: {activation.imei}, Service Type: {activation.service_type}")
        
        # Atualizar status
        previous_status = activation.status
        print(f"Previous status: {previous_status}")
        
        # Verificar se todos os documentos estão aprovados
        all_documents = Document.query.filter_by(activation_id=activation.id).all()
        all_documents_approved = all(doc.status == 'approved' for doc in all_documents) if all_documents else False
        
        # Decidir o próximo status baseado no estado atual e documentos
        if activation.status == "pendente_analise_documentos":
            if all_documents_approved:
                # Se documentos já aprovados e agora tem dados técnicos, vai direto para aprovado
                activation.status = "aprovado"
                activation.activation_date = datetime.utcnow()
                status_message = "Dados técnicos completados - ativação aprovada automaticamente"
            else:
                # Se documentos ainda não aprovados, vai para em_analise
                activation.status = "em_analise"
                status_message = "Dados técnicos completados pelo cliente"
        elif activation.status == "em_analise" and all_documents_approved:
            # Se estava em análise e agora tem dados técnicos completos, vai para aprovado
            activation.status = "aprovado"
            activation.activation_date = datetime.utcnow()
            status_message = "Dados técnicos completados - ativação aprovada automaticamente"
        else:
            # Mantém em análise
            activation.status = "em_analise"
            status_message = "Dados técnicos completados pelo cliente"
            
        print(f"Status updated to: {activation.status}")

        # Registrar histórico
        log_activation_change(
            activation.id, 
            previous_status, 
            activation.status, 
            user_id, 
            status_message
        )
        
        print(f"Committing changes to database...")
        db.session.commit()
        print(f"✅ Database commit successful")
        
        # Verificar se os dados foram realmente salvos
        db.session.refresh(activation)
        print(f"After commit verification - ICCID: {activation.iccid}, EID: {activation.eid}, IMEI: {activation.imei}, Service Type: {activation.service_type}")
        
        # Criar notificação baseada no status final
        if activation.status == "aprovado":
            create_notification(
                user_id,
                "Ativação Aprovada",
                "Dados técnicos enviados com sucesso. Sua ativação foi aprovada! Aguarde o envio do QR Code.",
                activation.id
            )
        else:
            create_notification(
                user_id,
                "Dados Técnicos Completados",
                "Dados técnicos enviados com sucesso. Sua ativação está em análise.",
                activation.id
            )
        
        return jsonify({
            "message": "Dados técnicos completados com sucesso",
            "activation": activation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@client_bp.route("/profile/documents", methods=["POST"])
@jwt_required()
def upload_profile_documents():
    """Upload de documentos para o perfil do usuário"""
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        try:
            user_uuid = UUID(user_id)  # For other models that use UUID
            user = User.query.get(user_id)  # User model uses String(36) for ID
        except ValueError:
            return jsonify({"error": "ID de usuário inválido"}), 400
        
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Verificar se os arquivos foram enviados
        if 'identity_front' not in request.files or 'identity_back' not in request.files or 'selfie_with_document' not in request.files:
            return jsonify({"error": "Todos os documentos são obrigatórios: identity_front, identity_back, selfie_with_document"}), 400
        
        identity_front = request.files['identity_front']
        identity_back = request.files['identity_back']
        selfie_with_document = request.files['selfie_with_document']
        
        # Validar arquivos
        files_to_validate = [
            ('identity_front', identity_front),
            ('identity_back', identity_back),
            ('selfie_with_document', selfie_with_document)
        ]
        
        for file_type, file in files_to_validate:
            if file.filename == '':
                return jsonify({"error": f"Arquivo {file_type} não selecionado"}), 400
            
            if not allowed_file(file.filename):
                return jsonify({"error": f"Tipo de arquivo não permitido para {file_type}"}), 400
        
        # Criar diretório para documentos do perfil se não existir
        profile_docs_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profile_documents', str(user_uuid))
        os.makedirs(profile_docs_dir, exist_ok=True)
        
        # Salvar arquivos
        saved_files = {}
        for file_type, file in files_to_validate:
            if file:
                filename = secure_filename(f"{file_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file_path = os.path.join(profile_docs_dir, filename)
                file.save(file_path)
                saved_files[file_type] = file_path
        
        # Atualizar usuário com os caminhos dos documentos
        user.identity_front_path = saved_files.get('identity_front')
        user.identity_back_path = saved_files.get('identity_back')
        user.selfie_with_document_path = saved_files.get('selfie_with_document')
        user.documents_uploaded_at = datetime.utcnow()
        user.documents_approved = False  # Resetar aprovação
        user.documents_approved_at = None
        user.documents_approved_by = None
        
        db.session.commit()
        
        return jsonify({
            "message": "Documentos do perfil enviados com sucesso",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@client_bp.route("/profile/documents", methods=["GET"])
@jwt_required()
def get_profile_documents():
    """Buscar documentos do perfil do usuário"""
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        try:
            user_uuid = UUID(user_id)  # For other models that use UUID
            user = User.query.get(user_id)  # User model uses String(36) for ID
        except ValueError:
            return jsonify({"error": "ID de usuário inválido"}), 400
        
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        documents_info = {
            "has_documents": bool(user.identity_front_path and user.identity_back_path and user.selfie_with_document_path),
            "documents_uploaded_at": user.documents_uploaded_at.isoformat() if user.documents_uploaded_at else None,
            "documents_approved": user.documents_approved,
            "documents_approved_at": user.documents_approved_at.isoformat() if user.documents_approved_at else None,
            "identity_front_path": user.identity_front_path,
            "identity_back_path": user.identity_back_path,
            "selfie_with_document_path": user.selfie_with_document_path
        }
        
        return jsonify(documents_info), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@client_bp.route("/activations/<activation_id>", methods=["GET"])
@jwt_required()
def get_activation(activation_id):
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        
        try:
            activation_uuid = UUID(activation_id)
            user_uuid = UUID(user_id)
            activation = Activation.query.filter_by(
                id=activation_uuid, 
                user_id=user_uuid
            ).first()
        except ValueError:
            return jsonify({"error": "ID inválido"}), 400
        
        if not activation:
            return jsonify({"error": "Ativação não encontrada"}), 404
        
        # Buscar documentos
        documents = Document.query.filter_by(activation_id=activation.id).all()
        
        # Buscar histórico
        history = ActivationHistory.query.filter_by(activation_id=activation.id).order_by(ActivationHistory.changed_at.desc()).all()
        
        return jsonify({
            "activation": activation.to_dict(),
            "documents": [doc.to_dict() for doc in documents],
            "history": [h.to_dict() for h in history]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/activations/<activation_id>/qr-scanned", methods=["POST"])
@jwt_required()
def confirm_qr_scanned(activation_id):
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        
        try:
            activation_uuid = UUID(activation_id)
            user_uuid = UUID(user_id)
            activation = Activation.query.filter_by(
                id=activation_uuid, 
                user_id=user_uuid
            ).first()
        except ValueError:
            return jsonify({"error": "ID inválido"}), 400
        
        if not activation:
            return jsonify({"error": "Ativação não encontrada"}), 404
        
        if activation.status != "pendente_confirmacao_qr":
            return jsonify({"error": "Ativação não está no status correto para confirmar QR Code"}), 400
        
        previous_status = activation.status
        activation.status = "ativada"
        activation.qr_scanned_at = datetime.utcnow()
        
        log_activation_change(
            activation.id, 
            previous_status, 
            "ativada", 
            user_id, 
            "Cliente confirmou escaneamento do QR Code"
        )
        db.session.commit()
        
        create_notification(
            user_id,
            "QR Code Confirmado",
            "Você confirmou o escaneamento do QR Code. Sua linha está ativa!",
            activation.id
        )
        
        return jsonify({"message": "Confirmação de QR Code registrada com sucesso", "activation": activation.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/ddds/<operator>", methods=["GET"])
@jwt_required()
def get_available_ddds(operator):
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        ddds = DDD.query.filter_by(operator=operator, is_active=True).all()
        return jsonify({"ddds": [d.to_dict() for d in ddds]}), 200
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        try:
            user_uuid = UUID(user_id)
            notifications = Notification.query.filter_by(user_id=user_uuid).order_by(Notification.created_at.desc()).all()
        except ValueError:
            return jsonify({"error": "ID de usuário inválido"}), 400
        return jsonify({"notifications": [n.to_dict() for n in notifications]}), 200
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@client_bp.route("/notifications/<notification_id>/read", methods=["POST"])
@jwt_required()
def mark_notification_read(notification_id):
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        try:
            notification_uuid = UUID(notification_id)
            user_uuid = UUID(user_id)
            notification = Notification.query.filter_by(id=notification_uuid, user_id=user_uuid).first()
        except ValueError:
            return jsonify({"error": "ID inválido"}), 400
        
        if not notification:
            return jsonify({"error": "Notificação não encontrada"}), 404
            
        notification.read_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Notificação marcada como lida"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

# Rota de upload de QR code pelo cliente removida - apenas admin pode fazer upload de QR code

@client_bp.route("/activations/<activation_id>/combined-pdf", methods=["GET"])
@jwt_required()
def download_combined_pdf(activation_id):
    """Gera e baixa PDF combinado com contrato e documentos"""
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        
        # Buscar ativação
        try:
            activation_uuid = UUID(activation_id)
            user_uuid = UUID(user_id)
            activation = Activation.query.filter_by(id=activation_uuid, user_id=user_uuid).first()
        except ValueError:
            return jsonify({"error": "ID inválido"}), 400
        if not activation:
            return jsonify({"error": "Ativação não encontrada"}), 404
        
        # Buscar usuário - User model uses String(36) for ID
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Buscar documentos da ativação
        documents = Document.query.filter_by(activation_id=activation_uuid).all()
        
        # Buscar dados de aceite de contrato
        contract_acceptance_data = None
        if activation.contract_acceptance_id:
            contract_acceptance = ContractAcceptance.query.get(activation.contract_acceptance_id)
            if contract_acceptance:
                contract_acceptance_data = contract_acceptance.to_dict()
        
        # Preparar dados
        activation_data = activation.to_dict()
        user_data = user.to_dict()
        documents_data = [doc.to_dict() for doc in documents]
        
        # Criar diretório para PDFs combinados se não existir
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "/tmp/uploads")
        combined_pdf_dir = os.path.join(upload_folder, "combined_pdfs")
        os.makedirs(combined_pdf_dir, exist_ok=True)
        
        # Nome do arquivo PDF combinado
        pdf_filename = f"ativacao_{activation_id}_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(combined_pdf_dir, pdf_filename)
        
        # Buscar caminhos dos documentos
        selfie_path = user.selfie_with_document_path
        identity_front_path = user.identity_front_path
        identity_back_path = user.identity_back_path
        
        # Gerar PDF combinado
        pdf_path = create_combined_pdf(
            selfie_path, 
            identity_front_path, 
            identity_back_path, 
            user.name, 
            user.cpf, 
            combined_pdf_dir
        )
        
        # Verificar se o arquivo foi criado
        if not os.path.exists(pdf_path):
            return jsonify({"error": "Erro ao gerar PDF combinado"}), 500
        
        # Salvar uma cópia do PDF combinado no perfil do cliente
        try:
            profile_docs_dir = os.path.join(upload_folder, "profile_documents", str(user_uuid))
            os.makedirs(profile_docs_dir, exist_ok=True)
            
            # Nome do arquivo no perfil
            profile_pdf_filename = f"ativacao_completa_{activation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            profile_pdf_path = os.path.join(profile_docs_dir, profile_pdf_filename)
            
            # Copiar o PDF para o perfil do cliente
            shutil.copy2(pdf_path, profile_pdf_path)
            
            # Atualizar o campo combined_pdf_path no usuário
            user.combined_pdf_path = profile_pdf_path
            db.session.commit()
            
            print(f"PDF combinado salvo no perfil do cliente: {profile_pdf_path}")
            
        except Exception as e:
            print(f"Erro ao salvar PDF combinado no perfil: {str(e)}")
            # Não falha a operação principal se não conseguir salvar no perfil
        
        # Registrar no histórico
        log_activation_change(
            activation_id=activation_uuid,
            previous_status=activation.status,
            new_status=activation.status,  # Mantém o mesmo status
            user_id=user_id,
            reason="PDF combinado gerado pelo cliente"
        )
        
        # Retornar arquivo para download
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Ativacao_{activation_id}_Completa.pdf"
        )
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@client_bp.route("/notifications/read-all", methods=["POST"])
@jwt_required()
def mark_all_notifications_read():
    try:
        auth_check = require_client()
        if auth_check:
            return auth_check
        
        user_id = get_jwt_identity()
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            return jsonify({"error": "ID de usuário inválido"}), 400
        
        # Buscar todas as notificações não lidas do usuário
        notifications = Notification.query \
            .filter_by(user_id=user_uuid) \
            .filter(Notification.read_at.is_(None)) \
            .all()
        
        if not notifications:
            return jsonify({"message": "Nenhuma notificação não lida"}), 200
        
        now = datetime.utcnow()
        for n in notifications:
            n.read_at = now
        
        db.session.commit()
        return jsonify({"message": "Notificações marcadas como lidas"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

