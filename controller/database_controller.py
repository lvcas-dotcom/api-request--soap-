"""
Database Controller - Controlador para operações de banco de dados
Coordena interações entre interface do usuário e serviços de banco
"""

from typing import Dict, Any, Optional
import os

from service.database_service import DatabaseService
from service.storage_service import FileStorageService
from interface.cli_interface import CLIInterface
from interface.styles.colors import Colors


class DatabaseController:
    """
    Controlador para operações de banco de dados
    Implementa padrão MVC para coordenar operações
    """

    def __init__(self):
        """Inicializa o controlador"""
        self.database_service = None
        self.file_service = FileStorageService()

    def inicializar_banco(self) -> bool:
        """
        Inicializa conexão e cria estrutura do banco

        Returns:
            True se inicializou com sucesso
        """
        try:
            print(Colors.info("⚙️ Inicializando sistema de banco de dados..."))

            # Inicializar serviço
            self.database_service = DatabaseService()

            # Criar schema e tabelas
            if self.database_service.criar_schema_banco():
                print(Colors.success("✅ Banco de dados inicializado com sucesso"))
                return True
            else:
                CLIInterface.mostrar_erro("❌ Erro ao criar estrutura do banco")
                return False

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro na inicialização: {e}")
            return False

    def processar_arquivo_json_para_banco(self, caminho_arquivo: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa arquivo JSON mais recente ou especificado para o banco

        Args:
            caminho_arquivo: Caminho específico ou None para usar o mais recente

        Returns:
            Resultado do processamento
        """
        if not self.database_service:
            if not self.inicializar_banco():
                return {'sucesso': False, 'erro': 'Falha ao inicializar banco'}

        try:
            # Determinar arquivo a processar
            if not caminho_arquivo:
                arquivos = self.file_service.listar_arquivos_salvos("completo")
                if not arquivos:
                    return {'sucesso': False, 'erro': 'Nenhum arquivo encontrado'}
                caminho_arquivo = arquivos[0]  # Mais recente

            # Garantir que caminho_arquivo não é None
            if not caminho_arquivo:
                return {'sucesso': False, 'erro': 'Nenhum arquivo especificado'}

            # Verificar se arquivo existe
            if not os.path.exists(caminho_arquivo):
                return {'sucesso': False, 'erro': f'Arquivo não encontrado: {caminho_arquivo}'}

            print(Colors.info(f"📂 Processando arquivo: {os.path.basename(caminho_arquivo)}"))

            # Processar arquivo (garantir que database_service existe)
            if self.database_service:
                resultado = self.database_service.processar_arquivo_json(caminho_arquivo)

                # Exibir resultado
                self._exibir_resultado_processamento(resultado)

                return resultado
            else:
                return {'sucesso': False, 'erro': 'Serviço de banco não inicializado'}

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro no processamento: {e}")
            return {'sucesso': False, 'erro': str(e)}

    def obter_estatisticas_banco(self) -> Dict[str, Any]:
        """
        Obtém e exibe estatísticas do banco de dados

        Returns:
            Estatísticas do banco
        """
        if not self.database_service:
            if not self.inicializar_banco():
                return {}

        try:
            if self.database_service:
                stats = self.database_service.obter_estatisticas_completas()

                if stats:
                    self._exibir_estatisticas_banco(stats)

                return stats
            else:
                return {}

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao obter estatísticas: {e}")
            return {}

    def testar_conexao_banco(self) -> bool:
        """
        Testa conexão com o banco de dados

        Returns:
            True se conexão está funcionando
        """
        try:
            if not self.database_service:
                self.database_service = DatabaseService()

            if self.database_service.testar_conexao():
                print(Colors.success("✅ Conexão com PostgreSQL OK"))
                return True
            else:
                CLIInterface.mostrar_erro("❌ Falha na conexão com PostgreSQL")
                return False

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao testar conexão: {e}")
            return False

    def listar_arquivos_disponiveis(self) -> Dict[str, Any]:
        """
        Lista arquivos JSON disponíveis para processamento

        Returns:
            Informações dos arquivos disponíveis
        """
        try:
            arquivos_completos = self.file_service.listar_arquivos_salvos("completo")
            arquivos_progresso = self.file_service.listar_arquivos_salvos("progresso")

            CLIInterface.mostrar_arquivo_salvo("📁 Arquivos disponíveis:")

            if arquivos_completos:
                print("\n🏆 Arquivos completos:")
                for i, arquivo in enumerate(arquivos_completos[:5], 1):
                    info = self.file_service.obter_informacoes_arquivo(arquivo)
                    if info:
                        print(f"  {i}. {info['nome']} ({info['tamanho_mb']} MB)")

            if arquivos_progresso:
                print("\n⏳ Arquivos de progresso:")
                for i, arquivo in enumerate(arquivos_progresso[:3], 1):
                    info = self.file_service.obter_informacoes_arquivo(arquivo)
                    if info:
                        print(f"  {i}. {info['nome']} ({info['tamanho_mb']} MB)")

            return {
                'completos': arquivos_completos,
                'progresso': arquivos_progresso
            }

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao listar arquivos: {e}")
            return {'completos': [], 'progresso': []}

    def _exibir_resultado_processamento(self, resultado: Dict[str, Any]):
        """Exibe resultado do processamento de forma organizada"""
        if resultado.get('sucesso'):
            print(Colors.success("🎉 Processamento concluído com sucesso!"))

            print(f"\n📊 Resumo do processamento:")
            print(f"  • Total de registros: {resultado.get('total_registros', 0)}")
            print(f"  • Inseridos: {resultado.get('inseridos', 0)}")
            print(f"  • Atualizados: {resultado.get('atualizados', 0)}")
            print(f"  • Erros: {resultado.get('erros', 0)}")

            tempo = resultado.get('tempo_processamento', 0)
            print(f"  • Tempo: {tempo:.2f} segundos")

            if resultado.get('erros', 0) > 0:
                erros_detalhes = resultado.get('erros_detalhes', [])
                print(f"\n⚠️ Alguns erros encontrados:")
                for erro in erros_detalhes[:5]:  # Mostrar até 5 erros
                    print(f"  • {erro}")
        else:
            CLIInterface.mostrar_erro("❌ Falha no processamento")
            erro = resultado.get('erro', 'Erro desconhecido')
            print(f"Erro: {erro}")

    def _exibir_estatisticas_banco(self, stats: Dict[str, Any]):
        """Exibe estatísticas do banco de forma organizada"""
        CLIInterface.mostrar_aviso("📊 Estatísticas do Banco de Dados:")

        print(f"  🏠 Cadastros: {stats.get('total_cadastros', 0)}")
        print(f"  👥 Proprietários: {stats.get('total_proprietarios', 0)}")
        print(f"  📍 Endereços: {stats.get('total_enderecos', 0)}")
        print(f"  🗺️ Zoneamentos: {stats.get('total_zoneamentos', 0)}")

    def executar_workflow_completo(self) -> Dict[str, Any]:
        """
        Executa workflow completo: inicializar banco + processar arquivo mais recente

        Returns:
            Resultado do workflow
        """
        try:
            CLIInterface.mostrar_aviso("🚀 Iniciando workflow completo de banco de dados...")

            # 1. Inicializar banco
            if not self.inicializar_banco():
                return {'sucesso': False, 'erro': 'Falha na inicialização do banco'}

            # 2. Processar arquivo mais recente
            resultado = self.processar_arquivo_json_para_banco()

            # 3. Exibir estatísticas finais
            if resultado.get('sucesso'):
                self.obter_estatisticas_banco()

            return resultado

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro no workflow: {e}")
            return {'sucesso': False, 'erro': str(e)}
