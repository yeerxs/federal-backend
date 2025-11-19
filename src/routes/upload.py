from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import pandas as pd
import hashlib
import os
from datetime import datetime
import unicodedata
import re

from models import DDDImport
from models.user import DDD
from config.database import db

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_hash(row):
    """Gera hash única normalizando campos relevantes"""
    linha_src = str(row.get('linha_original', row.get('linha', ''))).strip()
    linha_digits = ''.join(ch for ch in linha_src if ch.isdigit())
    operadora = str(row.get('operadora', '')).strip().lower()
    tipo = str(row.get('tipo_chip', '')).strip().lower()
    espec_raw = str(row.get('especificacao', '')).strip()
    espec_digits = re.sub(r'[^0-9]', '', espec_raw)
    ddd = str(row.get('ddd', '')).strip()
    base = f"{ddd}_{operadora}_{tipo}_{espec_digits}_{linha_digits}"
    return hashlib.sha256(base.encode()).hexdigest()

def validate_ddd_data(data):
    """Valida dados de DDD para cadastro manual"""
    errors = []
    
    # Validar DDD (2 dígitos)
    ddd = str(data.get('ddd', '')).strip()
    if not ddd or len(ddd) != 2 or not ddd.isdigit():
        errors.append('DDD deve ter exatamente 2 dígitos')
    
    # Validar operadora (obrigatória)
    operadora = str(data.get('operadora', '')).strip()
    if not operadora:
        errors.append('Operadora é obrigatória')
    
    # Validar tipo_chip (vazia ou smp)
    tipo_chip = str(data.get('tipo_chip', '')).strip().lower()
    if tipo_chip not in ['vazia', 'smp']:
        errors.append('Tipo de chip deve ser "vazia" ou "smp"')
    
    # Especificação opcional para cadastro manual
    
    return errors

def normalize_text(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()

def rename_columns(df):
    mapping = {}
    for col in df.columns:
        n = normalize_text(col)
        if 'ddd' in n:
            mapping[col] = 'ddd'
        elif 'operad' in n or 'carrier' in n:
            mapping[col] = 'operadora'
        elif ('tipo' in n and 'chip' in n) or n == 'tipo':
            mapping[col] = 'tipo_chip'
        elif 'especifica' in n or 'gb' in n or 'plano' in n:
            mapping[col] = 'especificacao'
        elif 'linha' in n or 'numero' in n or 'telefone' in n:
            mapping[col] = 'linha'
    if mapping:
        df = df.rename(columns=mapping)
    return df

@upload_bp.route('/upload-ddds', methods=['POST'])
@jwt_required()
def upload_ddds():
    try:
        # Obter arquivo do campo 'file' ou qualquer outro campo de arquivo enviado
        file = request.files.get('file')
        if not file and request.files:
            file = next(iter(request.files.values()))
        if not file:
            return jsonify({'error': 'Nenhum arquivo enviado. Envie multipart/form-data com o campo "file"'}), 400
        
        # Verificar se o arquivo foi selecionado
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        # Verificar extensão
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não permitido. Use .xlsx ou .xls'}), 400
        
        # Verificar tamanho do arquivo
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'Arquivo muito grande. Máximo 10MB'}), 400
        
        # Limpar importações anteriores
        db.session.query(DDDImport).delete()
        db.session.commit()

        # Ler arquivo Excel
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'Erro ao ler arquivo Excel: {str(e)}'}), 400
        
        # Verificar se tem pelo menos 4 colunas
        if len(df.columns) < 4:
            return jsonify({'error': 'Arquivo deve ter pelo menos 4 colunas'}), 400
        
        df = rename_columns(df)
        
        # Se não houver coluna 'linha', criar a partir da coluna 'ddd'
        if 'linha' not in df.columns and 'ddd' in df.columns:
            df['linha'] = df['ddd']
        if 'tipo_chip' not in df.columns:
            df['tipo_chip'] = 'vazia'
        if 'especificacao' not in df.columns:
            df['especificacao'] = '150GB'
        
        # Aplicar filtros
        linhas_filtradas = []
        rejeicoes = {"tipo_invalido": 0, "spec_invalida": 0, "linha_invalida": 0}
        
        for _, row in df.iterrows():
            # Filtro 1: Tipo chip
            tipo_chip_val = normalize_text(row.get('tipo_chip', ''))
            if tipo_chip_val not in ['vazia', 'vazio', 'smp']:
                rejeicoes["tipo_invalido"] += 1
                continue
            
            especificacao_raw = str(row.get('especificacao', '')).strip()
            digits_spec = re.sub(r'[^0-9]', '', especificacao_raw)
            if digits_spec != '150':
                rejeicoes["spec_invalida"] += 1
                continue
            
            # Extrair 2 primeiros dígitos da linha
            linha_raw = str(row.get('linha', str(row.get('ddd', '')))).strip()
            linha_digits = ''.join(ch for ch in linha_raw if ch.isdigit())
            if len(linha_digits) < 2:
                rejeicoes["linha_invalida"] += 1
                continue
            ddd = linha_digits[:2]
            
            # Dados da operadora
            operadora = str(row.get('operadora', '')).strip()
            
            # Criar dicionário com dados filtrados
            dados_filtrados = {
                'ddd': ddd,
                'operadora': operadora,
                'tipo_chip': tipo_chip_val,
                'especificacao': especificacao_raw,
                'linha_original': linha_raw,
                'arquivo_origem': secure_filename(file.filename)
            }
            
            linhas_filtradas.append(dados_filtrados)
        
        # Estatísticas
        total_linhas = len(df)
        linhas_filtradas_count = len(linhas_filtradas)
        
        if linhas_filtradas_count == 0:
            return jsonify({
                'error': 'Nenhuma linha atendeu aos critérios de filtro',
                'estatisticas': {
                    'total_linhas': total_linhas,
                    'linhas_filtradas': 0,
                    'linhas_rejeitadas': total_linhas
                },
                'detalhes_rejeicao': rejeicoes,
                'colunas_reconhecidas': list(df.columns)
            }), 400
        
        duplicatas = 0
        linhas_unicas = []
        hashes_vistos = set()
        
        for linha in linhas_filtradas:
            hash_linha = generate_hash(linha)
            existing = DDDImport.query.filter_by(hash_linha=hash_linha).first()
            if existing or hash_linha in hashes_vistos:
                duplicatas += 1
                continue
            hashes_vistos.add(hash_linha)
            linha['hash_linha'] = hash_linha
            linhas_unicas.append(linha)
        
        # Inserir no banco de dados
        novos_registros = 0
        for linha in linhas_unicas:
            ddd = DDDImport(
                ddd=linha['ddd'],
                operadora=linha['operadora'],
                tipo_chip=linha['tipo_chip'],
                especificacao=linha['especificacao'],
                linha_original=linha['linha_original'],
                arquivo_origem=linha['arquivo_origem'],
                hash_linha=linha['hash_linha']
            )
            db.session.add(ddd)
            novos_registros += 1
        
        # Commit das alterações
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Erro ao salvar no banco de dados: {str(e)}'}), 500

        # Sincronizar catálogo oficial
        def norm_op(op):
            s = (op or '').strip().lower()
            if s.startswith('vivo'):
                return 'vivo'
            if s.startswith('claro'):
                return 'claro'
            if s.startswith('tim'):
                return 'tim'
            return None

        target = set()
        for imp in DDDImport.query.all():
            op = norm_op(imp.operadora)
            if not op:
                continue
            ddd_value = (imp.ddd or '').strip()[:2]
            if len(ddd_value) != 2 or not ddd_value.isdigit():
                continue
            target.add((op, ddd_value))

        existing = {(d.operator, d.ddd): d for d in DDD.query.all()}

        to_remove = []
        to_add = []

        for (op, ddd_value), obj in existing.items():
            if (op, ddd_value) not in target:
                to_remove.append(obj)

        for op, ddd_value in target:
            if (op, ddd_value) not in existing:
                to_add.append((op, ddd_value))

        for obj in to_remove:
            db.session.delete(obj)

        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        try:
            from uuid import UUID
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        except Exception:
            user_uuid = None

        for op, ddd_value in to_add:
            db.session.add(DDD(operator=op, ddd=ddd_value, is_active=True, created_by=user_uuid))

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Arquivo processado e catálogo sincronizado',
            'estatisticas': {
                'total_linhas': total_linhas,
                'linhas_filtradas': linhas_filtradas_count,
                'duplicatas_encontradas': duplicatas,
                'novos_registros': novos_registros,
                'catalogo_adicionados': len(to_add),
                'catalogo_removidos': len(to_remove),
                'catalogo_total': DDD.query.count()
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500

@upload_bp.route('/ddds/manual', methods=['POST'])
@jwt_required()
def add_ddd_manual():
    """Adiciona um DDD manualmente"""
    try:
        data = request.get_json()
        
        # Validar dados
        errors = validate_ddd_data(data)
        if errors:
            return jsonify({'error': 'Validação falhou', 'errors': errors}), 400
        
        # Preparar dados
        ddd_data = {
            'ddd': str(data['ddd']).strip(),
            'operadora': str(data['operadora']).strip(),
            'tipo_chip': str(data['tipo_chip']).strip().lower(),
            'especificacao': str(data.get('especificacao', '')).strip(),
            'linha_original': str(data.get('ddd', '')).strip(),
            'arquivo_origem': 'MANUAL'
        }
        
        # Gerar hash
        hash_linha = generate_hash(ddd_data)
        
        # Verificar duplicata
        existing = DDDImport.query.filter_by(hash_linha=hash_linha).first()
        if existing:
            return jsonify({'error': 'DDD já existe no sistema'}), 409
        
        # Criar novo registro
        novo_ddd = DDDImport(
            ddd=ddd_data['ddd'],
            operadora=ddd_data['operadora'],
            tipo_chip=ddd_data['tipo_chip'],
            especificacao=ddd_data['especificacao'],
            linha_original=ddd_data['linha_original'],
            arquivo_origem=ddd_data['arquivo_origem'],
            hash_linha=hash_linha
        )
        
        db.session.add(novo_ddd)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'DDD adicionado com sucesso',
            'ddd': novo_ddd.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao adicionar DDD: {str(e)}'}), 500

@upload_bp.route('/ddds/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_ddd(id):
    """Remove um DDD pelo ID"""
    try:
        ddd = DDDImport.query.get(id)
        
        if not ddd:
            return jsonify({'error': 'DDD não encontrado'}), 404
        
        db.session.delete(ddd)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'DDD removido com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover DDD: {str(e)}'}), 500

@upload_bp.route('/ddds/preview', methods=['POST'])
@jwt_required()
def preview_ddds():
    """Preview de DDDs sem salvar no banco (para upload manual ou arquivo)"""
    try:
        # Verificar se é arquivo ou dados JSON
        if 'file' in request.files:
            # Preview de arquivo
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            
            if not allowed_file(file.filename):
                return jsonify({'error': 'Tipo de arquivo não permitido. Use .xlsx ou .xls'}), 400
            
            # Ler arquivo Excel
            try:
                df = pd.read_excel(file)
            except Exception as e:
                return jsonify({'error': f'Erro ao ler arquivo Excel: {str(e)}'}), 400
            
            # Verificar se tem pelo menos 4 colunas
            if len(df.columns) < 4:
                return jsonify({'error': 'Arquivo deve ter pelo menos 4 colunas'}), 400
            
            df = rename_columns(df)
            
            if 'linha' not in df.columns and 'ddd' in df.columns:
                df['linha'] = df['ddd']
            
            source_type = 'arquivo'
            source_name = secure_filename(file.filename)
            
        else:
            # Preview de dados JSON (manual)
            data = request.get_json()
            
            if not data or 'ddd' not in data:
                return jsonify({'error': 'Dados inválidos para preview'}), 400
            
            # Validar dados
            errors = validate_ddd_data(data)
            if errors:
                return jsonify({'error': 'Validação falhou', 'errors': errors}), 400
            
            # Criar DataFrame com um único registro
            df = pd.DataFrame([{
                'ddd': str(data['ddd']).strip(),
                'operadora': str(data['operadora']).strip(),
                'tipo_chip': str(data['tipo_chip']).strip().lower(),
                'especificacao': str(data.get('especificacao', '')).strip()
            }])
            
            source_type = 'manual'
            source_name = 'MANUAL'
        
        # Aplicar filtros
        linhas_filtradas = []
        
        for _, row in df.iterrows():
            # Filtro 1: Tipo chip deve ser "vazia" ou "smp"
            tipo_chip = str(row.get('tipo_chip', '')).strip().lower()
            if tipo_chip not in ['vazia', 'smp']:
                continue
            
            especificacao_raw = str(row.get('especificacao', '')).strip()
            digits_spec = re.sub(r'[^0-9]', '', especificacao_raw)
            if source_type == 'arquivo' and digits_spec != '150':
                continue
            
            # Extrair 2 primeiros dígitos da linha
            linha_raw = str(row.get('linha', str(row.get('ddd', '')))).strip()
            linha_digits = ''.join(ch for ch in linha_raw if ch.isdigit())
            if len(linha_digits) < 2:
                continue
            ddd = linha_digits[:2]
            
            # Dados da operadora
            operadora = str(row.get('operadora', '')).strip()
            
            # Criar dicionário com dados filtrados
            dados_filtrados = {
                'ddd': ddd,
                'operadora': operadora,
                'tipo_chip': tipo_chip,
                'especificacao': especificacao_raw,
                'linha_original': linha_raw,
                'arquivo_origem': source_name
            }
            
            linhas_filtradas.append(dados_filtrados)
        
        # Estatísticas
        total_linhas = len(df)
        linhas_filtradas_count = len(linhas_filtradas)
        
        # Verificar duplicatas (apenas para preview, não salva no banco)
        duplicatas = 0
        hashes_vistos = set()
        
        for linha in linhas_filtradas:
            hash_linha = generate_hash(linha)
            
            # Verificar se já existe no banco
            existing = DDDImport.query.filter_by(hash_linha=hash_linha).first()
            if existing or hash_linha in hashes_vistos:
                duplicatas += 1
            
            hashes_vistos.add(hash_linha)
        
        return jsonify({
            'success': True,
            'preview': {
                'source_type': source_type,
                'source_name': source_name,
                'ddds': linhas_filtradas[:50],  # Limitar a 50 para não sobrecarregar
                'total_preview': len(linhas_filtradas)
            },
            'estatisticas': {
                'total_linhas': total_linhas,
                'linhas_filtradas': linhas_filtradas_count,
                'linhas_rejeitadas': total_linhas - linhas_filtradas_count,
                'duplicatas_previstas': duplicatas
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar preview: {str(e)}'}), 500

@upload_bp.route('/ddds', methods=['GET'])
@jwt_required()
def get_ddds():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Query com paginação
        pagination = DDDImport.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        ddds = [ddd.to_dict() for ddd in pagination.items]
        
        return jsonify({
            'ddds': ddds,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar DDDs: {str(e)}'}), 500

@upload_bp.route('/ddds/estatisticas', methods=['GET'])
@jwt_required()
def get_ddds_stats():
    try:
        from sqlalchemy import func
        
        # Estatísticas gerais
        total = DDDImport.query.count()
        
        # Estatísticas por operadora
        operadoras = db.session.query(
            DDDImport.operadora,
            func.count(DDDImport.id).label('quantidade')
        ).group_by(DDDImport.operadora).all()
        
        # Estatísticas por DDD
        ddd_stats = db.session.query(
            DDDImport.ddd,
            func.count(DDDImport.id).label('quantidade')
        ).group_by(DDDImport.ddd).all()
        
        # Estatísticas por tipo de chip
        tipo_chip_stats = db.session.query(
            DDDImport.tipo_chip,
            func.count(DDDImport.id).label('quantidade')
        ).group_by(DDDImport.tipo_chip).all()
        
        return jsonify({
            'total': total,
            'operadoras': [{'operadora': op[0], 'quantidade': op[1]} for op in operadoras],
            'ddds': [{'ddd': ddd[0], 'quantidade': ddd[1]} for ddd in ddd_stats],
            'tipos_chip': [{'tipo_chip': tc[0], 'quantidade': tc[1]} for tc in tipo_chip_stats]
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar estatísticas: {str(e)}'}), 500
