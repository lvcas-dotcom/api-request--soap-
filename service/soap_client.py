"""
Cliente SOAP Completo para Integração Cadastral
Implementa todos os métodos do WSDL com tratamento de erros, retry e normalização de datas
"""

from zeep import Client, Settings
from zeep.helpers import serialize_object
from zeep.exceptions import Fault as SOAPFault
from requests.auth import HTTPBasicAuth
from requests import Session
from zeep.transports import Transport
import logging
import time
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date

from config.settings import settings
from model.data_models import *


class SOAPClientError(Exception):
    """Exceção específica para erros do cliente SOAP"""
    pass


def normalizar_data_brasileira(data_str):
    """
    Converte data brasileira DD/MM/YYYY para formato ISO YYYY-MM-DD
    Retorna None se não conseguir converter
    """
    if not data_str or data_str == "":
        return None
    
    # Padrões de data brasileira
    padroes = [
        r'(\d{2})/(\d{2})/(\d{4})',  # DD/MM/YYYY
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # D/M/YYYY ou DD/M/YYYY
    ]
    
    for padrao in padroes:
        match = re.match(padrao, str(data_str).strip())
        if match:
            dia, mes, ano = match.groups()
            try:
                # Validar data
                data_obj = datetime(int(ano), int(mes), int(dia))
                return data_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
    
    # Se não conseguiu converter, retorna string original
    return str(data_str)


def processar_dados_soap(dados):
    """
    Processa dados retornados do SOAP, normalizando datas e tipos
    """
    if isinstance(dados, dict):
        dados_processados = {}
        for chave, valor in dados.items():
            if isinstance(valor, (list, dict)):
                dados_processados[chave] = processar_dados_soap(valor)
            elif isinstance(valor, str) and ('data' in chave.lower() or 'date' in chave.lower()):
                # Tentar normalizar datas
                data_normalizada = normalizar_data_brasileira(valor)
                dados_processados[chave] = data_normalizada
            else:
                dados_processados[chave] = valor
        return dados_processados
    elif isinstance(dados, list):
        return [processar_dados_soap(item) for item in dados]
    else:
        return dados


class CadastralSOAPClient:
    """
    Cliente SOAP completo para integração cadastral
    Implementa todas as operações disponíveis no WSDL com tratamento robusto de erros
    """
    
    def __init__(self):
        """Inicializa cliente SOAP com configurações"""
        self.soap_config = settings.get_soap_config()
        self.logger = logging.getLogger(__name__)
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa cliente zeep com configurações otimizadas"""
        try:
            # Configurar sessão HTTP com autenticação
            session = Session()
            session.auth = HTTPBasicAuth(
                self.soap_config.username,
                self.soap_config.password
            )
            
            # Configurar transport
            transport = Transport(
                session=session,
                timeout=self.soap_config.timeout
            )
            
            # Inicializar cliente com configurações básicas
            self.client = Client(
                wsdl=self.soap_config.wsdl_path,
                transport=transport
            )
            
            self.logger.info("Cliente SOAP inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar cliente SOAP: {e}")
            raise SOAPClientError(f"Falha na inicialização do cliente SOAP: {e}")
    
    def _executar_com_retry(self, operacao_func, *args, **kwargs):
        """
        Executa operação SOAP com retry automático
        
        Args:
            operacao_func: Função da operação SOAP
            *args, **kwargs: Argumentos para a função
            
        Returns:
            Resultado da operação
        """
        ultimo_erro = None
        
        for tentativa in range(self.soap_config.max_retries):
            try:
                resultado = operacao_func(*args, **kwargs)
                return processar_dados_soap(serialize_object(resultado))
                
            except SOAPFault as e:
                ultimo_erro = e
                self.logger.warning(f"SOAP Fault na tentativa {tentativa + 1}: {e}")
                if tentativa < self.soap_config.max_retries - 1:
                    time.sleep(1 * (tentativa + 1))  # Backoff exponencial
                    
            except Exception as e:
                ultimo_erro = e
                self.logger.error(f"Erro na tentativa {tentativa + 1}: {e}")
                if tentativa < self.soap_config.max_retries - 1:
                    time.sleep(1 * (tentativa + 1))
        
        # Se chegou aqui, todas as tentativas falharam
        raise SOAPClientError(f"Operação falhou após {self.soap_config.max_retries} tentativas: {ultimo_erro}")
    
    def testar_conexao(self) -> bool:
        """
        Testa conectividade com o serviço SOAP
        
        Returns:
            True se conexão estiver funcionando
        """
        try:
            # Tentar busca simples para testar conectividade
            entrada = {
                'cpf_monitoracao': settings.cpf_monitoracao,
                'codigo_cadastro': '1-2',
                'inscricao_imobiliaria': '',
                'proprietario_cpfcnpj': '',
                'codigo_terreno': '',
                'data_hora_alteracao': '',
                'tipo_consulta': '1',
                'situacao': '1'
            }
            
            self._executar_com_retry(
                self.client.service.buscaCadastroImobiliarioGeral,
                entrada=entrada
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Teste de conexão falhou: {e}")
            return False
    
    def buscar_cadastro_geral(self, codigo_cadastro: str, tipo_consulta: int = 1, 
                             situacao: int = 1) -> List[Dict]:
        """
        Busca cadastros imobiliários de forma geral
        
        Args:
            codigo_cadastro: Código ou intervalo (ex: "123" ou "1-100")
            tipo_consulta: Tipo de consulta (padrão: 1)
            situacao: Situação do cadastro (padrão: 1)
            
        Returns:
            Lista de cadastros encontrados
        """
        entrada = {
            'cpf_monitoracao': settings.cpf_monitoracao,
            'codigo_cadastro': codigo_cadastro,
            'inscricao_imobiliaria': '',
            'proprietario_cpfcnpj': '',
            'codigo_terreno': '',
            'data_hora_alteracao': '',
            'tipo_consulta': str(tipo_consulta),
            'situacao': str(situacao)
        }
        
        try:
            response = self._executar_com_retry(
                self.client.service.buscaCadastroImobiliarioGeral,
                entrada=entrada
            )
            
            # Processar resposta
            cadastros = []
            if isinstance(response, dict):
                cadastros = response.get("cadastros", [])
            elif isinstance(response, list):
                cadastros = response
            
            return [item for item in cadastros if isinstance(item, dict)] if cadastros else []
            
        except Exception as e:
            self.logger.error(f"Erro na busca geral: {e}")
            raise SOAPClientError(f"Erro na busca geral de cadastros: {e}")
    
    def buscar_cadastro_especifico(self, codigo_cadastro: str) -> Optional[Dict]:
        """
        Busca um cadastro específico pelo código
        
        Args:
            codigo_cadastro: Código do cadastro
            
        Returns:
            Dados do cadastro ou None se não encontrado
        """
        cadastros = self.buscar_cadastro_geral(codigo_cadastro)
        return cadastros[0] if cadastros else None
    
    def buscar_proprietarios(self, codigo_cadastro: str) -> List[Dict]:
        """
        Busca proprietários de um cadastro específico
        
        Args:
            codigo_cadastro: Código do cadastro
            
        Returns:
            Lista de proprietários
        """
        try:
            response = self._executar_com_retry(
                self.client.service.buscaProprietarioBCI,
                codigoCadastro=codigo_cadastro
            )
            
            proprietarios = []
            if isinstance(response, dict):
                proprietarios = response.get("proprietarios", [])
            elif isinstance(response, list):
                proprietarios = response
                
            return [item for item in proprietarios if isinstance(item, dict)] if proprietarios else []
            
        except Exception as e:
            self.logger.error(f"Erro na busca de proprietários: {e}")
            return []
    
    def buscar_enderecos(self, codigo_cadastro: str) -> List[Dict]:
        """
        Busca endereços de um cadastro específico
        
        Args:
            codigo_cadastro: Código do cadastro
            
        Returns:
            Lista de endereços
        """
        try:
            response = self._executar_com_retry(
                self.client.service.buscaEnderecoBCI,
                codigoCadastro=codigo_cadastro
            )
            
            enderecos = []
            if isinstance(response, dict):
                enderecos = response.get("enderecos", [])
            elif isinstance(response, list):
                enderecos = response
                
            return [item for item in enderecos if isinstance(item, dict)] if enderecos else []
            
        except Exception as e:
            self.logger.error(f"Erro na busca de endereços: {e}")
            return []
    
    def buscar_testadas(self, codigo_cadastro: str) -> List[Dict]:
        """
        Busca testadas de um cadastro específico
        
        Args:
            codigo_cadastro: Código do cadastro
            
        Returns:
            Lista de testadas
        """
        try:
            response = self._executar_com_retry(
                self.client.service.buscaTestadaBCI,
                codigoCadastro=codigo_cadastro
            )
            
            testadas = []
            if isinstance(response, dict):
                testadas = response.get("testadas", [])
            elif isinstance(response, list):
                testadas = response
                
            return [item for item in testadas if isinstance(item, dict)] if testadas else []
            
        except Exception as e:
            self.logger.error(f"Erro na busca de testadas: {e}")
            return []
    
    def buscar_caracteristicas(self, codigo_cadastro: str) -> List[Dict]:
        """
        Busca características de um cadastro específico
        
        Args:
            codigo_cadastro: Código do cadastro
            
        Returns:
            Lista de características
        """
        try:
            response = self._executar_com_retry(
                self.client.service.buscaCaracteristicaBCI,
                codigoCadastro=codigo_cadastro
            )
            
            caracteristicas = []
            if isinstance(response, dict):
                caracteristicas = response.get("caracteristicas", [])
            elif isinstance(response, list):
                caracteristicas = response
                
            return [item for item in caracteristicas if isinstance(item, dict)] if caracteristicas else []
            
        except Exception as e:
            self.logger.error(f"Erro na busca de características: {e}")
            return []
    
    def buscar_subreceitas(self, codigo_cadastro: str) -> List[Dict]:
        """
        Busca subreceitas de um cadastro específico
        
        Args:
            codigo_cadastro: Código do cadastro
            
        Returns:
            Lista de subreceitas
        """
        try:
            response = self._executar_com_retry(
                self.client.service.buscaSubreceitaBCI,
                codigoCadastro=codigo_cadastro
            )
            
            subreceitas = []
            if isinstance(response, dict):
                subreceitas = response.get("subreceitas", [])
            elif isinstance(response, list):
                subreceitas = response
                
            return [item for item in subreceitas if isinstance(item, dict)] if subreceitas else []
            
        except Exception as e:
            self.logger.error(f"Erro na busca de subreceitas: {e}")
            return []
    
    def buscar_zoneamentos(self, codigo_cadastro: str) -> List[Dict]:
        """
        Busca zoneamentos de um cadastro específico
        
        Args:
            codigo_cadastro: Código do cadastro
            
        Returns:
            Lista de zoneamentos
        """
        try:
            response = self._executar_com_retry(
                self.client.service.buscaZoneamentoBCI,
                codigoCadastro=codigo_cadastro
            )
            
            zoneamentos = []
            if isinstance(response, dict):
                zoneamentos = response.get("zoneamentos", [])
            elif isinstance(response, list):
                zoneamentos = response
                
            return [item for item in zoneamentos if isinstance(item, dict)] if zoneamentos else []
            
        except Exception as e:
            self.logger.error(f"Erro na busca de zoneamentos: {e}")
            return []


# Funções auxiliares para operações futuras (CRUD)
# Estas serão implementadas quando necessário

def inserir_cadastro(dados_cadastro: Dict) -> bool:
    """Inserir novo cadastro (implementação futura)"""
    raise NotImplementedError("Operação de inserção será implementada em versão futura")

def atualizar_cadastro(codigo_cadastro: str, dados_atualizados: Dict) -> bool:
    """Atualizar cadastro existente (implementação futura)"""
    raise NotImplementedError("Operação de atualização será implementada em versão futura")

def excluir_cadastro(codigo_cadastro: str) -> bool:
    """Excluir cadastro (implementação futura)"""
    raise NotImplementedError("Operação de exclusão será implementada em versão futura")
