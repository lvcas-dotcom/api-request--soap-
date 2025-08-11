"""
Cadastro Service - Serviço de alto nível para extração de cadastros imobiliários
Usa o novo cliente SOAP completo e modelos de dados padronizados
"""

from typing import Dict, List, Any, Optional
import logging
import json
import os
import time
from datetime import datetime

from service.soap_client import CadastralSOAPClient, SOAPClientError
from service.cache_service import CacheService
from service.file_storage_service import FileStorageService
from service.statistics_service import StatisticsService
from model.data_models import CadastroImobiliario, dict_to_cadastro
from config.settings import settings
from interface.cli_interface import CLIInterface, ProgressTracker


class CadastroService:
    """
    Serviço orquestrador para extração completa de cadastros imobiliários
    Responsável por coordenar o fluxo de extração utilizando serviços especializados
    """
    
    def __init__(self):
        """Inicializa o serviço e seus componentes especializados"""
        self._setup_logging()
        self._initialize_client()
        self.app_config = settings.get_app_config()
        
        # Inicializar serviços especializados
        self.cache_service = CacheService()
        self.file_storage_service = FileStorageService(self.app_config.data_dir)
        self.statistics_service = StatisticsService()
    
    def _setup_logging(self):
        """Configura logging"""
        logging.getLogger('zeep').setLevel(logging.CRITICAL)
        logging.getLogger('isodate').setLevel(logging.CRITICAL)
    
    def _initialize_client(self):
        """Inicializa cliente SOAP"""
        try:
            self.soap_client = CadastralSOAPClient()
        except Exception as e:
            raise Exception(f"Erro ao inicializar cliente SOAP: {str(e)}")
    
    def extrair_todos_cadastros(self, codigo_inicio=0, codigo_fim=10000, intervalo_size=100):
        """
        Extrai TODOS os cadastros imobiliários do sistema usando nova arquitetura
        
        Args:
            codigo_inicio: Código inicial para busca
            codigo_fim: Código final para busca  
            intervalo_size: Tamanho de cada intervalo (máximo 100 por API)
        
        Returns:
            Resultado completo da extração
        """
        # Validar tamanho do intervalo
        if intervalo_size > self.app_config.max_interval_size:
            intervalo_size = self.app_config.max_interval_size
        
        # Preparar intervalos
        intervalos = self._gerar_intervalos(codigo_inicio, codigo_fim, intervalo_size)
        CLIInterface.mostrar_progresso_inicial(len(intervalos))
        
        # Inicializar tracking
        tracker = ProgressTracker(len(intervalos))
        todos_cadastros = []
        
        try:
            # Processar todos os intervalos
            for i, (inicio, fim) in enumerate(intervalos):
                # Buscar cadastros do intervalo
                cadastros_intervalo = self._buscar_por_intervalo(inicio, fim)
                
                # Atualizar progresso
                tracker.atualizar_intervalo(len(cadastros_intervalo))
                todos_cadastros.extend(cadastros_intervalo)
                
                # Mostrar progresso visual
                CLIInterface.mostrar_progresso_intervalo(
                    i + 1, len(intervalos), inicio, fim, len(cadastros_intervalo)
                )
                
                # Salvamento periódico usando o serviço especializado
                if len(todos_cadastros) > 0 and len(todos_cadastros) % self.app_config.save_interval == 0:
                    self.file_storage_service.salvar_progresso_parcial(todos_cadastros, sufixo="auto_backup")
                
                # Pausa entre requisições
                if i < len(intervalos) - 1:
                    time.sleep(self.app_config.request_delay)
            
            # Conclusão
            tempo_execucao = tracker.obter_tempo_decorrido()
            CLIInterface.mostrar_conclusao(
                len(todos_cadastros), 
                tracker.requisicoes_realizadas, 
                tempo_execucao
            )
            
            # Salvar resultado final usando o serviço especializado
            arquivo_final = None
            if todos_cadastros:
                # Gerar estatísticas para incluir nos metadados
                stats = self.statistics_service.gerar_estatisticas_completas(todos_cadastros)
                codigos_info = self.statistics_service.analisar_codigos_cadastro(todos_cadastros)
                
                metadados_extras = {
                    'estatisticas': stats,
                    'analise_codigos': codigos_info,
                    'total_requisicoes': tracker.requisicoes_realizadas,
                    'tempo_execucao': str(tempo_execucao)
                }
                
                arquivo_final = self.file_storage_service.salvar_resultado_final(
                    todos_cadastros, metadados_extras
                )
                
                # Exibir estatísticas usando dados já calculados
                CLIInterface.mostrar_estatisticas(stats, codigos_info)
            
            return {
                'sucesso': True,
                'cadastros': todos_cadastros,
                'total_cadastros': len(todos_cadastros),
                'total_requisicoes': tracker.requisicoes_realizadas,
                'tempo_execucao': tempo_execucao,
                'arquivo_salvo': arquivo_final
            }
            
        except KeyboardInterrupt:
            CLIInterface.mostrar_aviso("Operação interrompida pelo usuário")
            arquivo_parcial = None
            if todos_cadastros:
                arquivo_parcial = self.file_storage_service.salvar_progresso_parcial(
                    todos_cadastros, sufixo="interrupted"
                )
            return {
                'sucesso': False,
                'erro': 'Operação interrompida pelo usuário',
                'cadastros': todos_cadastros,
                'arquivo_salvo': arquivo_parcial
            }
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro durante extração: {e}")
            arquivo_parcial = None
            if todos_cadastros:
                arquivo_parcial = self.file_storage_service.salvar_progresso_parcial(
                    todos_cadastros, sufixo="error"
                )
            return {
                'sucesso': False,
                'erro': str(e),
                'cadastros': todos_cadastros,
                'arquivo_salvo': arquivo_parcial
            }
    
    def _gerar_intervalos(self, inicio, fim, tamanho):
        """Gera lista de intervalos para processamento"""
        intervalos = []
        for i in range(inicio, fim + 1, tamanho):
            intervalo_fim = min(i + tamanho - 1, fim)
            intervalos.append((i, intervalo_fim))
        return intervalos
    
    def _buscar_por_intervalo(self, codigo_inicio, codigo_fim):
        """
        Busca cadastros por intervalo específico usando novo cliente SOAP
        
        Args:
            codigo_inicio: Código inicial do intervalo
            codigo_fim: Código final do intervalo
            
        Returns:
            Lista de cadastros encontrados no intervalo
        """
        codigo_intervalo = f"{codigo_inicio}-{codigo_fim}"

        # Tentar carregar do cache
        cadastros_cache = self.cache_service.carregar_cache(codigo_intervalo)
        if cadastros_cache is not None:
            return cadastros_cache

        try:
            # Usar novo cliente SOAP
            cadastros_raw = self.soap_client.buscar_cadastro_geral(
                codigo_cadastro=codigo_intervalo,
                tipo_consulta=1,
                situacao=1
            )
            
            # Processar e normalizar dados
            cadastros_processados = []
            for cadastro_raw in cadastros_raw:
                cadastro_processado = self._processar_cadastro(cadastro_raw)
                if cadastro_processado:
                    cadastros_processados.append(cadastro_processado)

            # Salvar no cache
            self.cache_service.salvar_cache(codigo_intervalo, cadastros_processados)

            return cadastros_processados
            
        except SOAPClientError as e:
            CLIInterface.mostrar_erro(f"Erro SOAP no intervalo {codigo_intervalo}: {e}")
            return []
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro inesperado no intervalo {codigo_intervalo}: {e}")
            return []
    
    def _processar_cadastro(self, cadastro_raw):
        """
        Processa um cadastro individual, normalizando dados
        
        Args:
            cadastro_raw: Cadastro bruto da API
            
        Returns:
            Cadastro processado e normalizado
        """
        if not isinstance(cadastro_raw, dict):
            return None
        
        try:
            # Normalizar datas
            if 'data_cadastro' in cadastro_raw:
                cadastro_raw['data_cadastro'] = self._converter_data_brasileira(
                    cadastro_raw['data_cadastro']
                )
            
            # Normalizar campos numéricos
            for campo in ['area_terreno', 'area_construida', 'area_construida_averbada', 'area_total_construida']:
                if campo in cadastro_raw and cadastro_raw[campo]:
                    try:
                        cadastro_raw[campo] = float(str(cadastro_raw[campo]).replace(',', '.'))
                    except (ValueError, TypeError):
                        cadastro_raw[campo] = None
            
            # Garantir que listas vazias sejam tratadas corretamente
            for lista_campo in ['proprietariosbci', 'enderecos', 'testadas', 'caracteristicas', 'subreceitas', 'zoneamentos']:
                if lista_campo not in cadastro_raw or cadastro_raw[lista_campo] is None:
                    cadastro_raw[lista_campo] = []
            
            return cadastro_raw
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao processar cadastro: {e}")
            return None
    
    def _converter_data_brasileira(self, data_str):
        """
        Converte data do formato brasileiro DD/MM/YYYY para ISO YYYY-MM-DD
        
        Args:
            data_str: Data em formato brasileiro
            
        Returns:
            Data em formato ISO ou string original se conversão falhar
        """
        if not data_str or data_str == "":
            return None
        
        try:
            data_obj = datetime.strptime(data_str, "%d/%m/%Y")
            return data_obj.strftime("%Y-%m-%d")
        except ValueError:
            return data_str
    
    def buscar_cadastro_completo(self, codigo_cadastro: str) -> Optional[CadastroImobiliario]:
        """
        Busca cadastro completo com todos os dados relacionados
        
        Args:
            codigo_cadastro: Código do cadastro
            
        Returns:
            Objeto CadastroImobiliario completo ou None
        """
        try:
            # Buscar dados principais
            dados_principais = self.soap_client.buscar_cadastro_especifico(
                codigo_cadastro=codigo_cadastro
            )
            
            if not dados_principais:
                return None
            
            # Buscar dados relacionados
            proprietarios = self.soap_client.buscar_proprietarios(codigo_cadastro=codigo_cadastro)
            enderecos = self.soap_client.buscar_enderecos(codigo_cadastro)
            testadas = self.soap_client.buscar_testadas(codigo_cadastro)
            caracteristicas = self.soap_client.buscar_caracteristicas(codigo_cadastro)
            subreceitas = self.soap_client.buscar_subreceitas(codigo_cadastro)
            zoneamentos = self.soap_client.buscar_zoneamentos(codigo_cadastro)
            
            # Converter zoneamentos para objetos Zoneamento, se necessário
            from model.data_models import Zoneamento
            zoneamentos_objs = []
            for z in zoneamentos:
                if isinstance(z, Zoneamento):
                    zoneamentos_objs.append(z)
                elif isinstance(z, dict):
                    zoneamentos_objs.append(Zoneamento(**z))
                else:
                    continue
            
            # Montar objeto completo
            cadastro = dict_to_cadastro(dados_principais)
            from model.data_models import Proprietario, Endereco, Testada, BlocoItem, SubReceita

            cadastro.proprietarios = [Proprietario(**p) for p in proprietarios]
            cadastro.enderecos = [Endereco(**e) for e in enderecos]
            cadastro.testadas = [Testada(**t) for t in testadas]
            cadastro.caracteristicas = [BlocoItem(**c) for c in caracteristicas]
            cadastro.subreceitas = [SubReceita(**s) for s in subreceitas]
            cadastro.zoneamentos = zoneamentos_objs
            
            return cadastro
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao buscar cadastro completo: {e}")
            return None
    
    def testar_conexao(self) -> bool:
        """
        Testa conexão com o serviço SOAP
        
        Returns:
            True se conexão estiver funcionando
        """
        try:
            return self.soap_client.testar_conexao()
        except Exception:
            return False
    
    # Métodos públicos para acesso aos serviços especializados
    def obter_estatisticas_completas(self, cadastros):
        """
        Gera estatísticas completas usando o serviço especializado
        
        Args:
            cadastros: Lista de cadastros para análise
            
        Returns:
            Estatísticas completas
        """
        return self.statistics_service.gerar_estatisticas_completas(cadastros)
    
    def analisar_codigos_cadastro(self, cadastros):
        """
        Analisa códigos de cadastro usando o serviço especializado
        
        Args:
            cadastros: Lista de cadastros para análise
            
        Returns:
            Análise de códigos
        """
        return self.statistics_service.analisar_codigos_cadastro(cadastros)
    
    def salvar_dados_finais(self, cadastros, metadados=None):
        """
        Salva dados finais usando o serviço especializado
        
        Args:
            cadastros: Lista de cadastros
            metadados: Metadados opcionais
            
        Returns:
            Caminho do arquivo salvo
        """
        return self.file_storage_service.salvar_resultado_final(cadastros, metadados)
    
    def carregar_dados_salvos(self, caminho_arquivo):
        """
        Carrega dados salvos usando o serviço especializado
        
        Args:
            caminho_arquivo: Caminho do arquivo
            
        Returns:
            Dados carregados
        """
        return self.file_storage_service.carregar_dados_salvos(caminho_arquivo)
    
    def listar_arquivos_salvos(self, tipo="todos"):
        """
        Lista arquivos salvos usando o serviço especializado
        
        Args:
            tipo: Tipo de arquivo a listar
            
        Returns:
            Lista de arquivos
        """
        return self.file_storage_service.listar_arquivos_salvos(tipo)
