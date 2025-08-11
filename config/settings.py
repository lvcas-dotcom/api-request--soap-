"""
Configurações do Sistema de Integração SOAP
Centraliza todas as configurações e credenciais do sistema
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class SOAPConfig:
    """Configurações para conexão SOAP"""
    wsdl_path: str
    endpoint_url: str
    username: str
    password: str
    timeout: int = 30
    max_retries: int = 3


@dataclass
class AppConfig:
    """Configurações gerais da aplicação"""
    data_dir: str
    log_level: str
    save_interval: int
    max_interval_size: int
    request_delay: float


class Settings:
    """Classe principal para gerenciamento de configurações"""
    
    def __init__(self):
        self._load_settings()
    
    def _load_settings(self):
        """Carrega configurações do ambiente ou valores padrão"""
        
        # Configurações SOAP
        self.soap = SOAPConfig(
            wsdl_path=os.getenv('SOAP_WSDL_PATH', './wsdl/clevelandia.wsdl'),
            endpoint_url=os.getenv('SOAP_ENDPOINT', 
                'https://clevelandia.atende.net/?pg=services&service=WIPCadbciIntegracaoGeo&cidade=padrao'),
            username=os.getenv('SOAP_USERNAME', '18236979000167'),
            password=os.getenv('SOAP_PASSWORD', 'Tributech@2528'),
            timeout=int(os.getenv('SOAP_TIMEOUT', '30')),
            max_retries=int(os.getenv('SOAP_MAX_RETRIES', '3'))
        )
        
        # Configurações da aplicação
        self.app = AppConfig(
            data_dir=os.getenv('APP_DATA_DIR', './data'),
            log_level=os.getenv('APP_LOG_LEVEL', 'INFO'),
            save_interval=int(os.getenv('APP_SAVE_INTERVAL', '1000')),
            max_interval_size=int(os.getenv('APP_MAX_INTERVAL_SIZE', '100')),
            request_delay=float(os.getenv('APP_REQUEST_DELAY', '0.15'))
        )
        
        # CPF de monitoração
        self.cpf_monitoracao = os.getenv('CPF_MONITORACAO', '02644794919')
    
    def get_soap_config(self) -> SOAPConfig:
        """Retorna configurações SOAP"""
        return self.soap
    
    def get_app_config(self) -> AppConfig:
        """Retorna configurações da aplicação"""
        return self.app
    
    def get_cpf_monitoracao(self) -> str:
        """Retorna CPF de monitoração"""
        return self.cpf_monitoracao


# Instância global de configurações
settings = Settings()


# Constantes para tipos de operação (conforme WSDL)
class TipoOperacao:
    """Tipos de operação conforme documentação"""
    CONSULTA = 1
    INSERCAO = 2
    ALTERACAO = 3
    EXCLUSAO = 4


class TipoCadastro:
    """Tipos de cadastro conforme sistema"""
    TERRENO = 1
    EDIFICACAO = 2


class SituacaoCadastral:
    """Situações cadastrais válidas"""
    ATIVO = 1
    INATIVO = 2
    CANCELADO = 3


class TipoEndereco:
    """Tipos de endereço conforme sistema"""
    FISCAL = 1
    CORRESPONDENCIA = 2
    AMBOS = 3


class TipoProprietario:
    """Tipos de proprietário conforme sistema"""
    PROPRIETARIO = 1
    USUFRUTUARIO = 2
    LOCATARIO = 3
    OUTROS = 4


# Configurações de validação
VALIDATION_RULES = {
    'codigo_cadastro': {
        'type': str,
        'required': False,
        'max_length': 20
    },
    'inscricao_imobiliaria': {
        'type': str,
        'required': False,
        'pattern': r'^\d{2}\.\d{2}\.\d{3}\.\d{4}\.\d{3}$'
    },
    'cpf_cnpj': {
        'type': str,
        'required': False,
        'pattern': r'^\d{11}$|^\d{14}$'
    },
    'area_terreno': {
        'type': float,
        'required': False,
        'min_value': 0
    },
    'area_construida': {
        'type': float,
        'required': False,
        'min_value': 0
    }
}


# Mapeamento de campos para normalização
FIELD_MAPPING = {
    'codigo_cadastro': 'codigo_cadastro',
    'tipo_cadastro': 'tipo_cadastro',
    'situacao_cadastral': 'situacao_cadastral',
    'inscricao_imobiliaria': 'inscricao_imobiliaria',
    'area_terreno': 'area_terreno',
    'area_construida': 'area_construida',
    'data_cadastro': 'data_cadastro'
}


# Configurações de retry para requisições
RETRY_CONFIG = {
    'max_attempts': 3,
    'backoff_factor': 1.0,
    'backoff_max': 10.0,
    'retry_on_exceptions': [
        'ConnectionError',
        'Timeout',
        'SOAPFault'
    ]
}
