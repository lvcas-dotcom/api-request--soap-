"""
Modelos de Dados para Integração SOAP Cadastral
Define todas as estruturas de dados conforme WSDL
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum


class TipoCadastro(Enum):
    """Tipos de cadastro conforme sistema"""
    TERRENO = 1
    EDIFICACAO = 2


class SituacaoCadastral(Enum):
    """Situações cadastrais"""
    ATIVO = 1
    INATIVO = 2
    CANCELADO = 3


class TipoEndereco(Enum):
    """Tipos de endereço"""
    FISCAL = 1
    CORRESPONDENCIA = 2
    AMBOS = 3


class TipoProprietario(Enum):
    """Tipos de proprietário"""
    PROPRIETARIO = 1
    USUFRUTUARIO = 2
    LOCATARIO = 3
    OUTROS = 4


@dataclass
class Proprietario:
    """Modelo para proprietários (conforme WSDL proprietariosbci)"""
    codigo_pessoa: str
    codigo_cadastro: Optional[str] = None
    tipo_proprietario: int = 1
    situacao: int = 1
    percentual: Optional[str] = None
    data_ini_vigencia: Optional[date] = None
    data_fim_vigencia: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para envio SOAP"""
        return {
            'codigo_pessoa': self.codigo_pessoa,
            'codigo_cadastro': self.codigo_cadastro,
            'tipo_proprietario': self.tipo_proprietario,
            'situacao': self.situacao,
            'percentual': self.percentual,
            'data_ini_vigencia': self.data_ini_vigencia,
            'data_fim_vigencia': self.data_fim_vigencia
        }


@dataclass
class Endereco:
    """Modelo para endereços (conforme WSDL endereco)"""
    tipo_endereco: int
    codigo_cidade: int
    codigo_bairro: int
    codigo_logradouro: int
    cep: int
    descricao_cidade: Optional[str] = None
    descricao_bairro: Optional[str] = None
    descricao_logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    inf_complementar: Optional[str] = None
    garagem: Optional[str] = None
    sala: Optional[str] = None
    loja: Optional[str] = None
    codigo_loteamento: Optional[int] = None
    quadra: Optional[str] = None
    lote: Optional[str] = None
    codigo_edificio: Optional[int] = None
    bloco: Optional[str] = None
    nro_apto: Optional[int] = None
    coordenada_latitude: Optional[str] = None
    coordenada_longitude: Optional[str] = None
    coordenada_panorama: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para envio SOAP"""
        return {
            'tipo_endereco': self.tipo_endereco,
            'codigo_cidade': self.codigo_cidade,
            'codigo_bairro': self.codigo_bairro,
            'codigo_logradouro': self.codigo_logradouro,
            'cep': self.cep,
            'descricao_cidade': self.descricao_cidade,
            'descricao_bairro': self.descricao_bairro,
            'descricao_logradouro': self.descricao_logradouro,
            'numero': self.numero,
            'complemento': self.complemento,
            'inf_complementar': self.inf_complementar,
            'garagem': self.garagem,
            'sala': self.sala,
            'loja': self.loja,
            'codigo_loteamento': self.codigo_loteamento,
            'quadra': self.quadra,
            'lote': self.lote,
            'codigo_edificio': self.codigo_edificio,
            'bloco': self.bloco,
            'nro_apto': self.nro_apto,
            'coordenada_latitude': self.coordenada_latitude,
            'coordenada_longitude': self.coordenada_longitude,
            'coordenada_panorama': self.coordenada_panorama
        }


@dataclass
class Testada:
    """Modelo para testadas (conforme WSDL testada)"""
    numero_testada: int
    metragem: str
    codigo_secao: int
    id_secao: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para envio SOAP"""
        return {
            'numero_testada': self.numero_testada,
            'metragem': self.metragem,
            'codigo_secao': self.codigo_secao,
            'id_secao': self.id_secao
        }


@dataclass
class BlocoItem:
    """Modelo para características/bloco de itens (conforme WSDL blocoItem)"""
    codigo_bloco: int
    codigo_item: int
    sequencia_item: int
    valor: Optional[str] = None
    valor_lista: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para envio SOAP"""
        return {
            'codigo_bloco': self.codigo_bloco,
            'codigo_item': self.codigo_item,
            'sequencia_item': self.sequencia_item,
            'valor': self.valor,
            'valor_lista': self.valor_lista
        }


@dataclass
class SubReceita:
    """Modelo para sub-receitas (conforme WSDL subreceitacadbci)"""
    codigo_cadastro: int
    codigo_subreceita: int
    data_inicio_vigencia: date
    data_fim_vigencia: Optional[date] = None
    situacao: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para envio SOAP"""
        return {
            'codigo_cadastro': self.codigo_cadastro,
            'codigo_subreceita': self.codigo_subreceita,
            'data_inicio_vigencia': self.data_inicio_vigencia,
            'data_fim_vigencia': self.data_fim_vigencia,
            'situacao': self.situacao
        }


@dataclass
class Zoneamento:
    """Modelo para zoneamento (conforme WSDL zoneamento)"""
    codigo_zoneamento: Optional[int] = None
    observacao: str = ""
    principal: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para envio SOAP"""
        return {
            'codigo_zoneamento': self.codigo_zoneamento,
            'observacao': self.observacao,
            'principal': self.principal
        }


@dataclass
class CadastroImobiliario:
    """Modelo principal para cadastro imobiliário (conforme WSDL cadastrosbci)"""
    tipo_cadastro: int
    codigo_terreno: Optional[str] = None
    codigo_cadastro_global: Optional[str] = None
    inscricao_imobiliaria: Optional[str] = None
    inscricao_anterior: Optional[str] = None
    observacao: Optional[str] = None
    unico_cartorio: Optional[int] = None
    matricula: Optional[str] = None
    nro_livro: Optional[str] = None
    nro_folha: Optional[str] = None
    area_terreno: Optional[float] = None
    area_terreno_escriturada: Optional[float] = None
    profundidade: Optional[str] = None
    area_construida: Optional[float] = None
    area_construida_averbada: Optional[float] = None
    area_comum: Optional[float] = None
    afastamento_frontal: Optional[float] = None
    numero_pavimentos: Optional[int] = None
    nome_propriedade: Optional[str] = None
    numero_incra: Optional[int] = None
    numero_receita_federal: Optional[int] = None
    area_terreno_rural: Optional[float] = None
    area_terreno_escriturada_rural: Optional[float] = None
    area_construida_rural: Optional[float] = None
    area_construida_averbada_rural: Optional[float] = None
    tipo_medida: Optional[int] = None
    
    # Relacionamentos
    proprietarios: List[Proprietario] = field(default_factory=list)
    enderecos: List[Endereco] = field(default_factory=list)
    testadas: List[Testada] = field(default_factory=list)
    caracteristicas: List[BlocoItem] = field(default_factory=list)
    subreceitas: List[SubReceita] = field(default_factory=list)
    zoneamentos: List[Zoneamento] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para envio SOAP"""
        return {
            'tipo_cadastro': self.tipo_cadastro,
            'codigo_terreno': self.codigo_terreno,
            'codigo_cadastro_global': self.codigo_cadastro_global,
            'inscricao_imobiliaria': self.inscricao_imobiliaria,
            'inscricao_anterior': self.inscricao_anterior,
            'observacao': self.observacao,
            'unico_cartorio': self.unico_cartorio,
            'matricula': self.matricula,
            'nro_livro': self.nro_livro,
            'nro_folha': self.nro_folha,
            'area_terreno': self.area_terreno,
            'area_terreno_escriturada': self.area_terreno_escriturada,
            'profundidade': self.profundidade,
            'area_construida': self.area_construida,
            'area_construida_averbada': self.area_construida_averbada,
            'area_comum': self.area_comum,
            'afastamento_frontal': self.afastamento_frontal,
            'numero_pavimentos': self.numero_pavimentos,
            'nome_propriedade': self.nome_propriedade,
            'numero_incra': self.numero_incra,
            'numero_receita_federal': self.numero_receita_federal,
            'area_terreno_rural': self.area_terreno_rural,
            'area_terreno_escriturada_rural': self.area_terreno_escriturada_rural,
            'area_construida_rural': self.area_construida_rural,
            'area_construida_averbada_rural': self.area_construida_averbada_rural,
            'tipo_medida': self.tipo_medida,
            'proprietarios': [p.to_dict() for p in self.proprietarios],
            'enderecos': [e.to_dict() for e in self.enderecos],
            'testadas': [t.to_dict() for t in self.testadas],
            'caracteristicas': [c.to_dict() for c in self.caracteristicas],
            'subreceitas': [s.to_dict() for s in self.subreceitas],
            'zoneamentos': [z.to_dict() for z in self.zoneamentos]
        }


@dataclass
class HistoricoAlteracao:
    """Modelo para histórico de alterações"""
    data_hora: Optional[str] = None
    operacao: Optional[str] = None
    campo_alterado: Optional[str] = None
    informacao_anterior: Optional[str] = None
    informacao_nova: Optional[str] = None
    usuario: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'data_hora': self.data_hora,
            'operacao': self.operacao,
            'campo_alterado': self.campo_alterado,
            'informacao_anterior': self.informacao_anterior,
            'informacao_nova': self.informacao_nova,
            'usuario': self.usuario
        }


@dataclass
class Anexo:
    """Modelo para anexos"""
    nome: Optional[str] = None
    nome_download: Optional[str] = None
    tipo: Optional[str] = None
    conteudo: Optional[str] = None
    data: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'nome': self.nome,
            'nome_download': self.nome_download,
            'tipo': self.tipo,
            'conteudo': self.conteudo,
            'data': self.data
        }


@dataclass
class CampoAlteracao:
    """Modelo para campos de alteração"""
    nome_campo: Optional[str] = None
    valor: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'nome_campo': self.nome_campo,
            'valor': self.valor
        }


@dataclass
class RetornoOperacao:
    """Modelo genérico para retorno de operações SOAP"""
    sucesso: bool = False
    mensagem: Optional[str] = None
    codigo_cadastro: Optional[str] = None
    dados: Optional[Dict[str, Any]] = None
    erros: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'sucesso': self.sucesso,
            'mensagem': self.mensagem,
            'codigo_cadastro': self.codigo_cadastro,
            'dados': self.dados,
            'erros': self.erros
        }


# Funções utilitárias para conversão de dados

def dict_to_cadastro(data: Dict[str, Any]) -> CadastroImobiliario:
    """Converte dicionário em objeto CadastroImobiliario"""
    
    # Converter proprietários
    proprietarios = []
    if 'proprietariosbci' in data and data['proprietariosbci']:
        for prop_data in data['proprietariosbci']:
            proprietarios.append(Proprietario(**prop_data))
    
    # Converter endereços
    enderecos = []
    if 'enderecos' in data and data['enderecos']:
        for end_data in data['enderecos']:
            enderecos.append(Endereco(**end_data))
    
    # Converter testadas
    testadas = []
    if 'testadas' in data and data['testadas']:
        for test_data in data['testadas']:
            testadas.append(Testada(**test_data))
    
    # Converter características
    caracteristicas = []
    if 'caracteristicas' in data and data['caracteristicas']:
        for carac_data in data['caracteristicas']:
            caracteristicas.append(BlocoItem(**carac_data))
    
    # Converter sub-receitas
    subreceitas = []
    if 'subreceitas' in data and data['subreceitas']:
        for sub_data in data['subreceitas']:
            subreceitas.append(SubReceita(**sub_data))
    
    # Converter zoneamentos
    zoneamentos = []
    if 'zoneamentos' in data and data['zoneamentos']:
        for zone_data in data['zoneamentos']:
            zoneamentos.append(Zoneamento(**zone_data))
    
    # Criar objeto principal removendo listas que serão substituídas
    main_data = {k: v for k, v in data.items() 
                 if k not in ['proprietariosbci', 'enderecos', 'testadas', 
                             'caracteristicas', 'subreceitas', 'zoneamentos']}
    
    return CadastroImobiliario(
        **main_data,
        proprietarios=proprietarios,
        enderecos=enderecos,
        testadas=testadas,
        caracteristicas=caracteristicas,
        subreceitas=subreceitas,
        zoneamentos=zoneamentos
    )


def normalize_date_field(value: Any) -> Optional[date]:
    """Normaliza campo de data"""
    if not value:
        return None
    
    if isinstance(value, date):
        return value
    
    if isinstance(value, str):
        try:
            # Tentar formato brasileiro DD/MM/YYYY
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            try:
                # Tentar formato ISO YYYY-MM-DD
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
    
    return None


def normalize_float_field(value: Any) -> Optional[float]:
    """Normaliza campo numérico float"""
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        try:
            # Substituir vírgula por ponto se necessário
            normalized = value.replace(',', '.')
            return float(normalized)
        except ValueError:
            return None
    
    return None


def normalize_int_field(value: Any) -> Optional[int]:
    """Normaliza campo numérico int"""
    if value is None:
        return None
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, (str, float)):
        try:
            return int(value)
        except ValueError:
            return None
    
    return None
