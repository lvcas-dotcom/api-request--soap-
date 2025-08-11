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
from model.data_models import CadastroImobiliario, dict_to_cadastro
from config.settings import settings
from interface.cli_interface import CLIInterface, ProgressTracker


class CadastroService:
    """Serviço de alto nível para extração completa de cadastros imobiliários"""
    
    def __init__(self):
        """Inicializa o serviço"""
        self._setup_logging()
        self._initialize_client()
        self.app_config = settings.get_app_config()
        self.cache_service = CacheService()  # Inicializa o serviço de cache
    
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
                
                # Salvamento periódico
                if len(todos_cadastros) > 0 and len(todos_cadastros) % self.app_config.save_interval == 0:
                    self._salvar_progresso_parcial_interno(todos_cadastros)
                
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
            
            # Salvar resultado final
            arquivo_final = None
            if todos_cadastros:
                arquivo_final = self.salvar_resultado_final_interno(todos_cadastros)
                
                # Exibir estatísticas
                stats = self.obter_estatisticas_interno(todos_cadastros)
                codigos_info = self._analisar_codigos_interno(todos_cadastros)
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
                arquivo_parcial = self._salvar_progresso_parcial_interno(todos_cadastros, sufixo="interrupted")
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
                arquivo_parcial = self._salvar_progresso_parcial_interno(todos_cadastros, sufixo="error")
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
    
    def _salvar_progresso_parcial_interno(self, cadastros, sufixo=None):
        """Salva progresso parcial durante extração"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sufixo_str = f"_{sufixo}" if sufixo else ""
        arquivo = f"data/cadastros_progresso_{timestamp}{sufixo_str}.json"
        
        try:
            os.makedirs("data", exist_ok=True)
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(cadastros, f, ensure_ascii=False, indent=2)
            CLIInterface.mostrar_aviso(f"Progresso salvo em: {arquivo}")
            return arquivo
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar progresso: {e}")
            return None
    
    def salvar_resultado_final_interno(self, cadastros):
        """
        Salva resultado final da extração completa
        
        Args:
            cadastros: Lista completa de cadastros
            
        Returns:
            Nome do arquivo salvo
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = f"data/cadastros_completo_{timestamp}.json"
        
        try:
            os.makedirs("data", exist_ok=True)
            
            # Adicionar metadados
            resultado = {
                'metadados': {
                    'data_extracao': datetime.now().isoformat(),
                    'total_cadastros': len(cadastros),
                    'versao_sistema': '2.0'
                },
                'cadastros': cadastros
            }
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            
            CLIInterface.mostrar_aviso(f"Arquivo final salvo: {arquivo}")
            return arquivo
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar arquivo final: {e}")
            return None
    
    def obter_estatisticas_interno(self, cadastros):
        """
        Gera estatísticas dos cadastros extraídos
        
        Args:
            cadastros: Lista de cadastros
            
        Returns:
            Dictionary com estatísticas
        """
        if not cadastros:
            return {'total': 0}
        
        # Contadores básicos
        stats = {
            'total': len(cadastros),
            'com_proprietarios': 0,
            'com_enderecos': 0,
            'com_area_terreno': 0,
            'com_area_construida': 0,
            'tipos_situacao': {},
            'tipos_categoria': {},
            'zonas': {},
            'area_total_terrenos': 0,
            'area_total_construida': 0
        }
        
        for cadastro in cadastros:
            if isinstance(cadastro, dict):
                # Contagem de propriedades
                if cadastro.get('proprietariosbci'):
                    stats['com_proprietarios'] += 1
                
                if cadastro.get('enderecos'):
                    stats['com_enderecos'] += 1
                
                # Análise de áreas
                area_terreno = cadastro.get('area_terreno')
                if area_terreno and area_terreno > 0:
                    stats['com_area_terreno'] += 1
                    stats['area_total_terrenos'] += area_terreno
                
                area_construida = cadastro.get('area_construida')
                if area_construida and area_construida > 0:
                    stats['com_area_construida'] += 1
                    stats['area_total_construida'] += area_construida
                
                # Contagem de situações
                situacao = cadastro.get('situacao', 'Não informado')
                stats['tipos_situacao'][situacao] = stats['tipos_situacao'].get(situacao, 0) + 1
                
                # Contagem de categorias
                categoria = cadastro.get('categoria', 'Não informado')
                stats['tipos_categoria'][categoria] = stats['tipos_categoria'].get(categoria, 0) + 1
                
                # Contagem de zonas
                zoneamentos = cadastro.get('zoneamentos', [])
                for zone in zoneamentos:
                    if isinstance(zone, dict):
                        zona = zone.get('zona', 'Não informado')
                        stats['zonas'][zona] = stats['zonas'].get(zona, 0) + 1
        
        return stats
    
    def _analisar_codigos_interno(self, cadastros):
        """
        Analisa distribuição de códigos de cadastro
        
        Args:
            cadastros: Lista de cadastros
            
        Returns:
            Informações sobre códigos
        """
        if not cadastros:
            CLIInterface.mostrar_erro("Nenhum cadastro fornecido para análise.")
            return {
                'total': 0,
                'menor_codigo': None,
                'maior_codigo': None,
                'intervalo_cobertura': 0,
                'densidade_ocupacao': 0
            }
        
        codigos = []
        for cadastro in cadastros:
            if isinstance(cadastro, dict):
                codigo = cadastro.get('codigo_cadastro')
                if codigo is None:
                    CLIInterface.mostrar_erro(f"Cadastro sem 'codigo_cadastro': {cadastro}")
                    continue
                try:
                    codigo_int = int(codigo)
                    codigos.append(codigo_int)
                except (ValueError, TypeError):
                    CLIInterface.mostrar_erro(f"Valor inválido para 'codigo_cadastro': {codigo} no cadastro {cadastro}")
                    continue
        
        if not codigos:
            CLIInterface.mostrar_erro("Nenhum código válido encontrado nos cadastros.")
            return {
                'total': 0,
                'menor_codigo': None,
                'maior_codigo': None,
                'intervalo_cobertura': 0,
                'densidade_ocupacao': 0
            }
        
        try:
            menor_codigo = min(codigos)
            maior_codigo = max(codigos)
            intervalo_cobertura = maior_codigo - menor_codigo + 1
            densidade_ocupacao = len(codigos) / intervalo_cobertura * 100
            return {
                'total': len(codigos),
                'menor_codigo': menor_codigo,
                'maior_codigo': maior_codigo,
                'intervalo_cobertura': intervalo_cobertura,
                'densidade_ocupacao': densidade_ocupacao
            }
        except ValueError as e:
            CLIInterface.mostrar_erro(f"Erro ao calcular estatísticas de códigos: {e}")
            return {
                'total': len(codigos),
                'menor_codigo': None,
                'maior_codigo': None,
                'intervalo_cobertura': 0,
                'densidade_ocupacao': 0
            }
    
    def _salvar_progresso_parcial(self, cadastros, sufixo="progress"):
        """
        Salva progresso parcial da extração
        
        Args:
            cadastros: Lista de cadastros para salvar
            sufixo: Sufixo para identificar tipo de salvamento
        """
        try:
            os.makedirs("./data", exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"./data/cadastros_{sufixo}_{timestamp}.json"
            
            dados = {
                "metadados": {
                    "total_cadastros": len(cadastros),
                    "timestamp_salvamento": datetime.now().isoformat(),
                    "tipo_salvamento": sufixo,
                    "versao": "1.0_producao"
                },
                "cadastros": cadastros
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False, default=str)
            
            CLIInterface.mostrar_salvamento_progresso()
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar progresso: {e}")
    
    def salvar_resultado_final(self, cadastros, filename="cadastros_completo.json"):
        """
        Salva resultado final com metadados completos
        
        Args:
            cadastros: Lista completa de cadastros
            filename: Nome do arquivo final
        """
        try:
            os.makedirs("./data", exist_ok=True)
            filepath = f"./data/{filename}"
            
            # Gerar estatísticas para metadados
            stats = self.obter_estatisticas(cadastros)
            codigos_info = self._analisar_codigos(cadastros)
            
            dados_completos = {
                "metadados": {
                    "total_cadastros": len(cadastros),
                    "data_extracao": datetime.now().isoformat(),
                    "metodo_extracao": "intervalos_oficiais_producao",
                    "versao_sistema": "2.0",
                    "estatisticas": stats,
                    "analise_codigos": codigos_info,
                    "validacao_completa": True
                },
                "cadastros": cadastros
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dados_completos, f, indent=2, ensure_ascii=False, default=str)
            
            return filepath
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar resultado final: {e}")
            return None
    
    def _analisar_codigos(self, cadastros):
        """Analisa distribuição e características dos códigos extraídos"""
        codigos = []
        for cadastro in cadastros:
            codigo = cadastro.get('codigo_cadastro')
            if codigo and str(codigo).isdigit():
                codigos.append(int(codigo))
        
        if not codigos:
            return {}
        
        codigos.sort()
        return {
            "menor": min(codigos),
            "maior": max(codigos),
            "unicos": len(set(codigos)),
            "densidade": (len(codigos) / (max(codigos) - min(codigos) + 1)) * 100 if codigos else 0,
            "range_total": max(codigos) - min(codigos) + 1 if codigos else 0
        }
    
    def obter_estatisticas(self, cadastros):
        """
        Gera estatísticas detalhadas dos cadastros extraídos
        
        Args:
            cadastros: Lista de cadastros para análise
            
        Returns:
            Dicionário com estatísticas completas
        """
        if not cadastros:
            return {"total": 0, "tipos": {}, "situacoes": {}}
        
        tipos = {}
        situacoes = {}
        
        for cadastro in cadastros:
            # Análise de tipos
            tipo = cadastro.get('tipo_cadastro')
            if tipo:
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            # Análise de situações
            situacao = cadastro.get('situacao_cadastral')
            if situacao:
                situacoes[situacao] = situacoes.get(situacao, 0) + 1
        
        return {
            "total": len(cadastros),
            "tipos": tipos,
            "situacoes": situacoes
        }
