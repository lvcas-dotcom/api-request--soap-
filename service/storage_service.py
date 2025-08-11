"""
File Storage Service - Gerencia toda a lógica de persistência e salvamento de dados
Responsável por salvar arquivos de progresso, resultados finais e manipulação de dados
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from interface.cli_interface import CLIInterface


class FileStorageService:
    """
    Serviço especializado em persistência e manipulação de arquivos
    Centraliza toda a lógica de salvamento de dados do sistema
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Inicializa o serviço de armazenamento
        
        Args:
            data_dir: Diretório base para salvamento de dados
        """
        self.data_dir = data_dir
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Garante que o diretório de dados existe"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def salvar_progresso_parcial(self, cadastros: List[Dict[str, Any]], sufixo: Optional[str] = None) -> Optional[str]:
        """
        Salva progresso parcial durante a extração
        
        Args:
            cadastros: Lista de cadastros para salvar
            sufixo: Sufixo opcional para identificar o tipo de salvamento
            
        Returns:
            Caminho do arquivo salvo ou None em caso de erro
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sufixo_str = f"_{sufixo}" if sufixo else ""
        arquivo = os.path.join(self.data_dir, f"cadastros_progresso_{timestamp}{sufixo_str}.json")
        
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(cadastros, f, ensure_ascii=False, indent=2)
            
            CLIInterface.mostrar_aviso(f"Progresso salvo em: {arquivo}")
            return arquivo
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar progresso: {e}")
            return None
    
    def salvar_resultado_final(self, cadastros: List[Dict[str, Any]], 
                              metadados: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Salva resultado final da extração completa com metadados
        
        Args:
            cadastros: Lista completa de cadastros
            metadados: Metadados adicionais para incluir no arquivo
            
        Returns:
            Caminho do arquivo salvo ou None em caso de erro
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(self.data_dir, f"cadastros_completo_{timestamp}.json")
        
        try:
            # Preparar metadados padrão
            metadados_completos = {
                'data_extracao': datetime.now().isoformat(),
                'total_cadastros': len(cadastros),
                'versao_sistema': '2.0',
                'metodo_extracao': 'intervalos_automatizados'
            }
            
            # Mesclar com metadados fornecidos
            if metadados:
                metadados_completos.update(metadados)
            
            # Estrutura final do arquivo
            resultado = {
                'metadados': metadados_completos,
                'cadastros': cadastros
            }
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            
            CLIInterface.mostrar_aviso(f"Arquivo final salvo: {arquivo}")
            return arquivo
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar arquivo final: {e}")
            return None
    
    def salvar_com_backup_automatico(self, cadastros: List[Dict[str, Any]], 
                                   total_processados: int, save_interval: int) -> Optional[str]:
        """
        Verifica e executa backup automático baseado no intervalo configurado
        
        Args:
            cadastros: Lista atual de cadastros
            total_processados: Total de cadastros processados até o momento
            save_interval: Intervalo para salvamento automático
            
        Returns:
            Caminho do arquivo salvo se backup foi executado, None caso contrário
        """
        if total_processados > 0 and total_processados % save_interval == 0:
            return self.salvar_progresso_parcial(cadastros, sufixo="auto_backup")
        return None
    
    def carregar_dados_salvos(self, caminho_arquivo: str) -> Optional[Dict[str, Any]]:
        """
        Carrega dados de um arquivo salvo anteriormente
        
        Args:
            caminho_arquivo: Caminho para o arquivo a ser carregado
            
        Returns:
            Dados carregados ou None em caso de erro
        """
        try:
            if not os.path.exists(caminho_arquivo):
                CLIInterface.mostrar_erro(f"Arquivo não encontrado: {caminho_arquivo}")
                return None
            
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            CLIInterface.mostrar_aviso(f"Dados carregados de: {caminho_arquivo}")
            return dados
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao carregar dados: {e}")
            return None
    
    def listar_arquivos_salvos(self, tipo: str = "todos") -> List[str]:
        """
        Lista arquivos salvos no diretório de dados
        
        Args:
            tipo: Tipo de arquivo ('progresso', 'completo', 'todos')
            
        Returns:
            Lista de caminhos de arquivos encontrados
        """
        try:
            arquivos = []
            for arquivo in os.listdir(self.data_dir):
                if tipo == "todos":
                    if arquivo.startswith("cadastros_"):
                        arquivos.append(os.path.join(self.data_dir, arquivo))
                elif tipo == "progresso":
                    if arquivo.startswith("cadastros_progresso_"):
                        arquivos.append(os.path.join(self.data_dir, arquivo))
                elif tipo == "completo":
                    if arquivo.startswith("cadastros_completo_"):
                        arquivos.append(os.path.join(self.data_dir, arquivo))
            
            return sorted(arquivos, reverse=True)  # Mais recentes primeiro
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao listar arquivos: {e}")
            return []
    
    def obter_informacoes_arquivo(self, caminho_arquivo: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações básicas sobre um arquivo salvo
        
        Args:
            caminho_arquivo: Caminho do arquivo
            
        Returns:
            Dicionário com informações do arquivo ou None
        """
        try:
            if not os.path.exists(caminho_arquivo):
                return None
            
            stat = os.stat(caminho_arquivo)
            nome_arquivo = os.path.basename(caminho_arquivo)
            
            # Tentar extrair informações do nome do arquivo
            info = {
                'nome': nome_arquivo,
                'caminho': caminho_arquivo,
                'tamanho_bytes': stat.st_size,
                'tamanho_mb': round(stat.st_size / (1024 * 1024), 2),
                'data_modificacao': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'tipo': 'progresso' if 'progresso' in nome_arquivo else 'completo'
            }
            
            # Tentar carregar metadados se disponível
            try:
                dados = self.carregar_dados_salvos(caminho_arquivo)
                if dados and 'metadados' in dados:
                    info['metadados'] = dados['metadados']
                if dados and 'cadastros' in dados:
                    info['total_cadastros'] = len(dados['cadastros'])
            except:
                pass  # Ignorar erros ao carregar metadados
            
            return info
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao obter informações do arquivo: {e}")
            return None
    
    def limpar_arquivos_antigos(self, manter_ultimos: int = 5) -> int:
        """
        Remove arquivos antigos mantendo apenas os mais recentes
        
        Args:
            manter_ultimos: Número de arquivos mais recentes para manter
            
        Returns:
            Número de arquivos removidos
        """
        try:
            arquivos = self.listar_arquivos_salvos("todos")
            
            if len(arquivos) <= manter_ultimos:
                return 0
            
            arquivos_para_remover = arquivos[manter_ultimos:]
            removidos = 0
            
            for arquivo in arquivos_para_remover:
                try:
                    os.remove(arquivo)
                    removidos += 1
                except Exception as e:
                    CLIInterface.mostrar_erro(f"Erro ao remover {arquivo}: {e}")
            
            if removidos > 0:
                CLIInterface.mostrar_aviso(f"Removidos {removidos} arquivos antigos")
            
            return removidos
            
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro na limpeza de arquivos: {e}")
            return 0
    
    def validar_integridade_arquivo(self, caminho_arquivo: str) -> bool:
        """
        Valida a integridade de um arquivo salvo
        
        Args:
            caminho_arquivo: Caminho do arquivo para validar
            
        Returns:
            True se arquivo é válido, False caso contrário
        """
        try:
            if not os.path.exists(caminho_arquivo):
                return False
            
            # Tentar carregar como JSON
            dados = self.carregar_dados_salvos(caminho_arquivo)
            if not dados:
                return False
            
            # Validações básicas
            if 'cadastros' not in dados:
                return False
            
            if not isinstance(dados['cadastros'], list):
                return False
            
            # Validar se há pelo menos um cadastro válido
            if len(dados['cadastros']) > 0:
                primeiro_cadastro = dados['cadastros'][0]
                if not isinstance(primeiro_cadastro, dict):
                    return False
            
            return True
            
        except Exception:
            return False
