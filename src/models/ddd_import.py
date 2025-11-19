from datetime import datetime
from sqlalchemy import func
import hashlib

# Importar db do módulo de configuração do banco de dados
from config.database import db

class DDDImport(db.Model):
    __tablename__ = 'ddd_imports'
    
    id = db.Column(db.Integer, primary_key=True)
    ddd = db.Column(db.String(2), nullable=False, index=True)  # Dois primeiros dígitos
    operadora = db.Column(db.String(100), nullable=False)
    tipo_chip = db.Column(db.String(50), nullable=False)  # "vazia" ou "smp"
    especificacao = db.Column(db.String(50), nullable=False)  # "150GB"
    linha_original = db.Column(db.String(20), nullable=False)  # Linha completa original
    
    # Dados de importação
    arquivo_origem = db.Column(db.String(255), nullable=False)
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Controle de duplicatas
    hash_linha = db.Column(db.String(64), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<DDDImport {self.ddd} - {self.operadora} - {self.tipo_chip}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ddd': self.ddd,
            'operadora': self.operadora,
            'tipo_chip': self.tipo_chip,
            'especificacao': self.especificacao,
            'linha_original': self.linha_original,
            'arquivo_origem': self.arquivo_origem,
            'data_importacao': self.data_importacao.isoformat() if self.data_importacao else None
        }
    
    @staticmethod
    def generate_hash(linha, operadora, tipo_chip, especificacao):
        """Gera um hash único para a linha com base nos dados"""
        data = f"{linha}:{operadora}:{tipo_chip}:{especificacao}"
        return hashlib.sha256(data.encode()).hexdigest()