from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
import os
from uuid import UUID

from models.user import db, Activation, Document

activation_bp = Blueprint('activation', __name__)

@activation_bp.route('/documents/<document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('user_type')
        
        try:
            document_uuid = UUID(document_id)
            document = Document.query.get(document_uuid)
        except ValueError:
            return jsonify({'error': 'ID de documento inválido'}), 400
        
        if not document:
            return jsonify({'error': 'Documento não encontrado'}), 404
        
        activation = document.activation
        
        # Verificar permissões
        if user_type == 'cliente':
            # Cliente só pode ver seus próprios documentos
            try:
                user_uuid = UUID(user_id)
                if activation.user_id != user_uuid:
                    return jsonify({'error': 'Acesso negado'}), 403
            except ValueError:
                return jsonify({'error': 'ID de usuário inválido'}), 400
        elif user_type != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Verificar se arquivo existe
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'Arquivo não encontrado no servidor'}), 404
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.file_name
        )
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@activation_bp.route('/qr-code/<activation_id>', methods=['GET'])
@jwt_required()
def get_qr_code(activation_id):
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('user_type')
        
        try:
            activation_uuid = UUID(activation_id)
            activation = Activation.query.get(activation_uuid)
        except ValueError:
            return jsonify({'error': 'ID de ativação inválido'}), 400
        
        if not activation:
            return jsonify({'error': 'Ativação não encontrada'}), 404
        
        # Verificar permissões
        if user_type == 'cliente':
            # Cliente só pode ver seu próprio QR Code
            try:
                user_uuid = UUID(user_id)
                if activation.user_id != user_uuid:
                    return jsonify({'error': 'Acesso negado'}), 403
            except ValueError:
                return jsonify({'error': 'ID de usuário inválido'}), 400
        elif user_type != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Verificar se QR Code existe
        if not activation.qr_code_path:
            return jsonify({'error': 'QR Code não disponível'}), 404
        
        if not os.path.exists(activation.qr_code_path):
            return jsonify({'error': 'Arquivo QR Code não encontrado no servidor'}), 404
        
        return send_file(
            activation.qr_code_path,
            as_attachment=False,
            mimetype='image/png'
        )
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@activation_bp.route('/contract', methods=['GET'])
@jwt_required()
def get_contract():
    try:
        # Retornar contrato padrão
        # Em um sistema real, isso viria de um arquivo ou banco de dados
        contract_text = """
CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE TELECOMUNICAÇÕES
FEDERAL ASSOCIADOS

1. OBJETO
O presente contrato tem por objeto a prestação de serviços de telecomunicações móveis.

2. PARTES
CONTRATANTE: Cliente identificado no sistema
CONTRATADA: Federal Associados

3. SERVIÇOS
A CONTRATADA se compromete a fornecer serviços de ativação de linha móvel conforme solicitado.

4. OBRIGAÇÕES DO CLIENTE
- Fornecer documentação verdadeira e atualizada
- Utilizar os serviços de acordo com os termos legais
- Efetuar pagamentos conforme acordado

5. OBRIGAÇÕES DA CONTRATADA
- Ativar a linha conforme especificações técnicas
- Manter sigilo das informações do cliente
- Prestar suporte técnico quando necessário

6. PRAZO
O prazo para ativação é de até 48 horas úteis após aprovação da documentação.

7. RESCISÃO
O contrato pode ser rescindido por qualquer das partes mediante comunicação prévia.

8. FORO
Fica eleito o foro da comarca de São Paulo para dirimir questões oriundas deste contrato.

Data: {data_atual}
Versão: 1.0
        """.format(data_atual=datetime.now().strftime('%d/%m/%Y'))
        
        return jsonify({
            'contract_text': contract_text,
            'version': '1.0'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


