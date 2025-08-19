"""
Database Models - Modelos de entidades para PostgreSQL
Define as tabelas e relacionamentos do banco de dados
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Boolean,
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class CadastroImobiliario(Base):
    """Tabela principal de cadastros imobiliários"""
    __tablename__ = 'cadastros_imobiliarios'
    __table_args__ = (
        Index('idx_codigo_cadastro', 'codigo_cadastro'),
        Index('idx_situacao', 'situacao'),
        Index('idx_categoria', 'categoria'),
        {'schema': 'public'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_cadastro = Column(String(50), unique=True, nullable=False)
    situacao = Column(String(100))
    categoria = Column(String(100))
    tipo_cadastro = Column(Integer)
    area_terreno = Column(Float)
    area_construida = Column(Float)
    area_construida_averbada = Column(Float)
    area_total_construida = Column(Float)
    data_cadastro = Column(String(20))

    # Campos de auditoria
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Dados JSON original para preservar estrutura completa
    dados_originais = Column(JSON)

    # Relacionamentos
    proprietarios = relationship("Proprietario", back_populates="cadastro", cascade="all, delete-orphan")
    enderecos = relationship("Endereco", back_populates="cadastro", cascade="all, delete-orphan")
    zoneamentos = relationship("Zoneamento", back_populates="cadastro", cascade="all, delete-orphan")

    ativo = Column(Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define o valor de "ativo" com base em "situacao"
        self.ativo = self.situacao == "1"

        # Define o valor de "categoria" com base em "tipo_cadastro"
        tipo_cadastro_map = {
            1: "terreno",
            2: "unidade",
            3: "rural"
        }
        self.categoria = tipo_cadastro_map.get(self.tipo_cadastro, "desconhecido")


class Proprietario(Base):
    """Tabela de proprietários"""
    __tablename__ = 'proprietarios'
    __table_args__ = (
        Index('idx_cadastro_proprietario', 'cadastro_id'),
        {'schema': 'public'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    cadastro_id = Column(Integer, ForeignKey('public.cadastros_imobiliarios.id', ondelete='CASCADE'))
    codigo_pessoa = Column(String(50))
    tipo_proprietario = Column(Integer)
    situacao = Column(Integer)
    percentual = Column(String(20))

    # Relacionamento
    cadastro = relationship("CadastroImobiliario", back_populates="proprietarios")


class Endereco(Base):
    """Tabela de endereços"""
    __tablename__ = 'enderecos'
    __table_args__ = (
        Index('idx_cadastro_endereco', 'cadastro_id'),
        {'schema': 'public'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    cadastro_id = Column(Integer, ForeignKey('public.cadastros_imobiliarios.id', ondelete='CASCADE'))
    tipo_endereco = Column(Integer)
    codigo_cidade = Column(Integer)
    codigo_bairro = Column(Integer)
    codigo_logradouro = Column(Integer)
    cep = Column(String(10))
    descricao_cidade = Column(String(100))
    descricao_bairro = Column(String(100))
    descricao_logradouro = Column(String(200))
    numero = Column(String(20))
    complemento = Column(String(100))

    # Relacionamento
    cadastro = relationship("CadastroImobiliario", back_populates="enderecos")


class Zoneamento(Base):
    """Tabela de zoneamentos"""
    __tablename__ = 'zoneamentos'
    __table_args__ = (
        Index('idx_cadastro_zoneamento', 'cadastro_id'),
        {'schema': 'public'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    cadastro_id = Column(Integer, ForeignKey('public.cadastros_imobiliarios.id', ondelete='CASCADE'))
    codigo_zoneamento = Column(Integer)
    observacao = Column(Text)
    principal = Column(Integer, default=0)

    # Relacionamento
    cadastro = relationship("CadastroImobiliario", back_populates="zoneamentos")


class ProcessamentoLog(Base):
    """Log de processamentos realizados"""
    __tablename__ = 'processamento_logs'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    arquivo_origem = Column(String(255), nullable=False)
    total_registros = Column(Integer)
    registros_inseridos = Column(Integer)
    registros_atualizados = Column(Integer)
    registros_erro = Column(Integer)
    tempo_processamento = Column(Float)  # em segundos
    status = Column(String(50))  # 'sucesso', 'erro', 'parcial'
    erro_detalhes = Column(Text)

    # Auditoria
    processado_em = Column(DateTime, default=func.now())
    processado_por = Column(String(100), default='sistema')
