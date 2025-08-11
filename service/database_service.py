"""
Database Service - Serviço de integração com banco de dados
Orquestra operações de banco mantendo lógica de negócio
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import time
from datetime import datetime

from config.database import db_settings
from repository.database_repository import DatabaseRepository
from model.database_models import Base
from interface.cli_interface import CLIInterface
from interface.styles.colors import Colors


class DatabaseService:
    """
    Serviço especializado em operações de banco de dados
    Implementa lógica de negócio para persistência de dados
    """

    def __init__(self):
        """Inicializa o serviço de banco de dados"""
        self.config = db_settings.get_database_config()
        self.engine = None
        self.Session = None
        self._initialize_database()

    def _initialize_database(self):
        """Inicializa conexão com banco de dados"""
        try:
            self.engine = create_engine(
                self.config.connection_string,
                echo=False,  # Set True para debug SQL
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )

            self.Session = sessionmaker(bind=self.engine)

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao conectar com PostgreSQL: {e}")
            raise

    def criar_schema_banco(self) -> bool:
        """
        Cria schema e tabelas no banco de dados

        Returns:
            True se criou com sucesso
        """
        try:
            # Criar schema se não existir
            with self.engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.config.schema}"))
                conn.commit()

            # Criar todas as tabelas
            Base.metadata.create_all(self.engine)

            print(Colors.success(f"✅ Schema '{self.config.schema}' criado com sucesso"))
            return True

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao criar schema: {e}")
            return False

    @contextmanager
    def get_db_session(self):
        """
        Context manager para sessões de banco
        Garante que a sessão seja fechada adequadamente
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            CLIInterface.mostrar_erro(f"Erro na sessão de banco: {e}")
            raise
        finally:
            session.close()

    def processar_arquivo_json(self, caminho_arquivo: str) -> Dict[str, Any]:
        """
        Processa arquivo JSON e insere dados no banco

        Args:
            caminho_arquivo: Caminho para arquivo JSON

        Returns:
            Resultado do processamento
        """
        inicio_tempo = time.time()

        try:
            # Carregar dados do arquivo
            from service.storage_service import FileStorageService
            file_service = FileStorageService()
            dados = file_service.carregar_dados_salvos(caminho_arquivo)

            if not dados or 'cadastros' not in dados:
                return {'sucesso': False, 'erro': 'Arquivo inválido ou sem cadastros'}

            cadastros = dados['cadastros']

            # Processar dados
            resultado = self._processar_lote_cadastros(cadastros, caminho_arquivo)

            # Calcular tempo de processamento
            tempo_total = time.time() - inicio_tempo
            resultado['tempo_processamento'] = tempo_total

            return resultado

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao processar arquivo: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'tempo_processamento': time.time() - inicio_tempo
            }

    def _processar_lote_cadastros(self, cadastros: List[Dict[str, Any]], arquivo_origem: str) -> Dict[str, Any]:
        """
        Processa lote de cadastros com controle de transação

        Args:
            cadastros: Lista de cadastros para processar
            arquivo_origem: Nome do arquivo de origem

        Returns:
            Resultado do processamento
        """
        total_registros = len(cadastros)
        inseridos = 0
        atualizados = 0
        erros = 0
        erros_detalhes = []

        try:
            with self.get_db_session() as session:
                repository = DatabaseRepository(session)

                print(Colors.info(f"📊 Processando {total_registros} cadastros..."))

                for i, cadastro in enumerate(cadastros):
                    try:
                        codigo_cadastro = cadastro.get('codigo_cadastro')

                        if not codigo_cadastro:
                            erros += 1
                            erros_detalhes.append("Cadastro sem código")
                            continue

                        # Verificar se já existe
                        if repository.verificar_cadastro_existe(codigo_cadastro):
                            # Atualizar existente
                            if repository.atualizar_cadastro(codigo_cadastro, cadastro):
                                atualizados += 1
                            else:
                                erros += 1
                                erros_detalhes.append(f"Erro ao atualizar {codigo_cadastro}")
                        else:
                            # Inserir novo
                            if repository.inserir_cadastro_completo(cadastro):
                                inseridos += 1
                            else:
                                erros += 1
                                erros_detalhes.append(f"Erro ao inserir {codigo_cadastro}")

                        # Mostrar progresso a cada 100 registros
                        if (i + 1) % 100 == 0:
                            CLIInterface.mostrar_progresso_banco(i + 1, total_registros, "Inserindo registros")

                    except Exception as e:
                        erros += 1
                        erros_detalhes.append(f"Erro no registro {i}: {str(e)}")

                # Registrar log do processamento
                log_data = {
                    'arquivo_origem': arquivo_origem,
                    'total_registros': total_registros,
                    'registros_inseridos': inseridos,
                    'registros_atualizados': atualizados,
                    'registros_erro': erros,
                    'status': 'sucesso' if erros == 0 else ('parcial' if inseridos + atualizados > 0 else 'erro'),
                    'erro_detalhes': '\n'.join(erros_detalhes[:10])  # Limitar erros salvos
                }

                repository.registrar_processamento(log_data)

                # Quebra de linha após progresso completo
                print()  # Nova linha após a barra de progresso

                return {
                    'sucesso': True,
                    'total_registros': total_registros,
                    'inseridos': inseridos,
                    'atualizados': atualizados,
                    'erros': erros,
                    'erros_detalhes': erros_detalhes
                }

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro durante processamento em lote: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'total_registros': total_registros,
                'inseridos': inseridos,
                'atualizados': atualizados,
                'erros': erros + 1
            }

    def obter_estatisticas_completas(self) -> Dict[str, Any]:
        """
        Obtém estatísticas completas do banco de dados

        Returns:
            Estatísticas detalhadas
        """
        try:
            with self.get_db_session() as session:
                repository = DatabaseRepository(session)
                return repository.obter_estatisticas_banco()

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao obter estatísticas: {e}")
            return {}

    def testar_conexao(self) -> bool:
        """
        Testa conexão com o banco de dados

        Returns:
            True se conexão está funcionando
        """
        try:
            with self.get_db_session() as session:
                session.execute(text("SELECT 1"))
                return True

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro na conexão: {e}")
            return False

    def limpar_dados(self, confirmar: bool = False) -> bool:
        """
        Limpa todos os dados das tabelas (CUIDADO!)

        Args:
            confirmar: Deve ser True para confirmar a operação

        Returns:
            True se limpou com sucesso
        """
        if not confirmar:
            CLIInterface.mostrar_erro("Operação não confirmada")
            return False

        try:
            with self.get_db_session() as session:
                # Limpar tabelas na ordem correta (relacionamentos)
                session.execute(text("DELETE FROM cadastros.zoneamentos"))
                session.execute(text("DELETE FROM cadastros.enderecos"))
                session.execute(text("DELETE FROM cadastros.proprietarios"))
                session.execute(text("DELETE FROM cadastros.cadastros_imobiliarios"))
                session.execute(text("DELETE FROM cadastros.processamento_logs"))

                print(Colors.success("✅ Dados limpos com sucesso"))
                return True

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao limpar dados: {e}")
            return False
