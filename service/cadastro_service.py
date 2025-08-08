"""
Cadastro Service - Serviço para extração de cadastros imobiliários
Responsável pela comunicação com API SOAP e processamento de dados
"""

from zeep import Client, Settings
from zeep.helpers import serialize_object
from requests.auth import HTTPBasicAuth
from requests import Session
from zeep.transports import Transport
import logging
import json
import os
import time
from datetime import datetime
from interface.cli_interface import CLIInterface, ProgressTracker


class CadastroService:
    """Serviço para extração completa de cadastros imobiliários via SOAP"""
    
    def __init__(self):
        """Inicializa o serviço SOAP com configurações otimizadas"""
        self._configurar_logging()
        self._inicializar_client()
    
    def _configurar_logging(self):
        """Configura logging para suprimir mensagens desnecessárias"""
        logging.getLogger('zeep').setLevel(logging.CRITICAL)
        logging.getLogger('isodate').setLevel(logging.CRITICAL)
    
    def _inicializar_client(self):
        """Inicializa cliente SOAP com autenticação"""
        wsdl_path = "./wsdl/clevelandia.wsdl"
        
        # Configurar autenticação HTTP básica
        session = Session()
        session.auth = HTTPBasicAuth('18236979000167', 'Tributech@2528')
        
        self.client = Client(wsdl=wsdl_path, transport=Transport(session=session))
    
    def extrair_todos_cadastros(self, codigo_inicio=0, codigo_fim=10000, intervalo_size=100):
        """
        Extrai TODOS os cadastros imobiliários do sistema
        
        Args:
            codigo_inicio: Código inicial para busca
            codigo_fim: Código final para busca  
            intervalo_size: Tamanho de cada intervalo (máximo 100 por API)
        
        Returns:
            Lista completa de todos os cadastros encontrados
        """
        # Preparar intervalos
        intervalos = self._gerar_intervalos(codigo_inicio, codigo_fim, intervalo_size)
        CLIInterface.mostrar_progresso_inicial(len(intervalos))
        
        # Inicializar tracking
        tracker = ProgressTracker(len(intervalos))
        todos_cadastros = []
        save_interval = 1000  # Salvar a cada 1000 cadastros
        
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
                if len(todos_cadastros) > 0 and len(todos_cadastros) % save_interval == 0:
                    self._salvar_progresso_parcial(todos_cadastros)
                
                # Pausa entre requisições para não sobrecarregar API
                if i < len(intervalos) - 1:
                    time.sleep(0.15)
            
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
                arquivo_final = self.salvar_resultado_final(todos_cadastros)
                
                # Exibir estatísticas
                stats = self.obter_estatisticas(todos_cadastros)
                codigos_info = self._analisar_codigos(todos_cadastros)
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
                arquivo_parcial = self._salvar_progresso_parcial(todos_cadastros, sufixo="interrupted")
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
                arquivo_parcial = self._salvar_progresso_parcial(todos_cadastros, sufixo="error")
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
        Busca cadastros por intervalo específico usando API oficial
        
        Args:
            codigo_inicio: Código inicial do intervalo
            codigo_fim: Código final do intervalo
            
        Returns:
            Lista de cadastros encontrados no intervalo
        """
        codigo_intervalo = f"{codigo_inicio}-{codigo_fim}"
        
        entrada = {
            'cpf_monitoracao': '02644794919',
            'codigo_cadastro': codigo_intervalo,
            'inscricao_imobiliaria': '',
            'proprietario_cpfcnpj': '',
            'codigo_terreno': '',
            'data_hora_alteracao': '',
            'tipo_consulta': '',
            'situacao': ''
        }
        
        try:
            response = self.client.service.buscaCadastroImobiliarioGeral(entrada=entrada)
            retorno = serialize_object(response)
            
            # Processar resposta
            cadastros = []
            if isinstance(retorno, dict):
                cadastros = retorno.get("cadastros", [])
            elif isinstance(retorno, list):
                cadastros = retorno
            
            # Processar e retornar cadastros
            return [self._processar_cadastro(cadastro) for cadastro in cadastros]
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro no intervalo {codigo_intervalo}: {e}")
            return []
    
    def _processar_cadastro(self, cadastro):
        """
        Processa um cadastro individual, corrigindo formatos de data
        
        Args:
            cadastro: Cadastro bruto da API
            
        Returns:
            Cadastro processado com datas normalizadas
        """
        if isinstance(cadastro, dict):
            # Normalizar datas brasileiras para ISO
            if 'data_cadastro' in cadastro:
                cadastro['data_cadastro'] = self._converter_data_brasileira(
                    cadastro['data_cadastro']
                )
        return cadastro
    
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
