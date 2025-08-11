"""
Database Repository - Camada de acesso aos dados (Repository Pattern)
Implementa operações de banco de dados de forma limpa e testável
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager
import time
from datetime import datetime

from model.database_models import (
    CadastroImobiliario, Proprietario, Endereco,
    Zoneamento, ProcessamentoLog
)
from interface.cli_interface import CLIInterface


class DatabaseRepository:
    """
    Repository para operações de banco de dados
    Implementa padrão Repository para abstração de acesso aos dados
    """

    def __init__(self, session: Session):
        """
        Inicializa o repository com uma sessão de banco

        Args:
            session: Sessão SQLAlchemy ativa
        """
        self.session = session

    def inserir_cadastro_completo(self, dados_cadastro: Dict[str, Any]) -> Optional[int]:
        """
        Insere um cadastro completo com todos os relacionamentos

        Args:
            dados_cadastro: Dados do cadastro em formato dict

        Returns:
            ID do cadastro inserido ou None em caso de erro
        """
        try:
            # Criar registro principal
            cadastro = CadastroImobiliario(
                codigo_cadastro=dados_cadastro.get('codigo_cadastro'),
                situacao=dados_cadastro.get('situacao'),
                categoria=dados_cadastro.get('categoria'),
                tipo_cadastro=dados_cadastro.get('tipo_cadastro'),
                area_terreno=self._parse_float(dados_cadastro.get('area_terreno')),
                area_construida=self._parse_float(dados_cadastro.get('area_construida')),
                area_construida_averbada=self._parse_float(dados_cadastro.get('area_construida_averbada')),
                area_total_construida=self._parse_float(dados_cadastro.get('area_total_construida')),
                data_cadastro=dados_cadastro.get('data_cadastro'),
                dados_originais=dados_cadastro  # Preservar dados originais
            )

            self.session.add(cadastro)
            self.session.flush()  # Para obter o ID

            # Inserir proprietários
            self._inserir_proprietarios(cadastro.id, dados_cadastro.get('proprietariosbci', []))

            # Inserir endereços
            self._inserir_enderecos(cadastro.id, dados_cadastro.get('enderecos', []))

            # Inserir zoneamentos
            self._inserir_zoneamentos(cadastro.id, dados_cadastro.get('zoneamentos', []))

            return cadastro.id

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao inserir cadastro {dados_cadastro.get('codigo_cadastro', 'N/A')}: {e}")
            return None

    def _inserir_proprietarios(self, cadastro_id: int, proprietarios: List[Dict[str, Any]]):
        """Insere proprietários associados ao cadastro"""
        for prop_data in proprietarios:
            if isinstance(prop_data, dict):
                proprietario = Proprietario(
                    cadastro_id=cadastro_id,
                    codigo_pessoa=prop_data.get('codigo_pessoa'),
                    tipo_proprietario=prop_data.get('tipo_proprietario'),
                    situacao=prop_data.get('situacao'),
                    percentual=prop_data.get('percentual')
                )
                self.session.add(proprietario)

    def _inserir_enderecos(self, cadastro_id: int, enderecos: List[Dict[str, Any]]):
        """Insere endereços associados ao cadastro"""
        for end_data in enderecos:
            if isinstance(end_data, dict):
                endereco = Endereco(
                    cadastro_id=cadastro_id,
                    tipo_endereco=end_data.get('tipo_endereco'),
                    codigo_cidade=end_data.get('codigo_cidade'),
                    codigo_bairro=end_data.get('codigo_bairro'),
                    codigo_logradouro=end_data.get('codigo_logradouro'),
                    cep=str(end_data.get('cep', '')),
                    descricao_cidade=end_data.get('descricao_cidade'),
                    descricao_bairro=end_data.get('descricao_bairro'),
                    descricao_logradouro=end_data.get('descricao_logradouro'),
                    numero=end_data.get('numero'),
                    complemento=end_data.get('complemento')
                )
                self.session.add(endereco)

    def _inserir_zoneamentos(self, cadastro_id: int, zoneamentos: List[Dict[str, Any]]):
        """Insere zoneamentos associados ao cadastro"""
        for zone_data in zoneamentos:
            if isinstance(zone_data, dict):
                zoneamento = Zoneamento(
                    cadastro_id=cadastro_id,
                    codigo_zoneamento=zone_data.get('codigo_zoneamento'),
                    observacao=zone_data.get('observacao'),
                    principal=zone_data.get('principal', 0)
                )
                self.session.add(zoneamento)

    def verificar_cadastro_existe(self, codigo_cadastro: str) -> bool:
        """
        Verifica se um cadastro já existe no banco

        Args:
            codigo_cadastro: Código do cadastro para verificar

        Returns:
            True se existe, False caso contrário
        """
        return self.session.query(CadastroImobiliario).filter(
            CadastroImobiliario.codigo_cadastro == codigo_cadastro
        ).first() is not None

    def atualizar_cadastro(self, codigo_cadastro: str, novos_dados: Dict[str, Any]) -> bool:
        """
        Atualiza um cadastro existente

        Args:
            codigo_cadastro: Código do cadastro
            novos_dados: Novos dados para atualizar

        Returns:
            True se atualizou com sucesso
        """
        try:
            cadastro = self.session.query(CadastroImobiliario).filter(
                CadastroImobiliario.codigo_cadastro == codigo_cadastro
            ).first()

            if not cadastro:
                return False

            # Atualizar campos principais
            for campo, valor in novos_dados.items():
                if hasattr(cadastro, campo) and campo != 'id':
                    setattr(cadastro, campo, valor)

            # Atualizar timestamp
            cadastro.updated_at = datetime.now()

            return True

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao atualizar cadastro {codigo_cadastro}: {e}")
            return False

    def obter_estatisticas_banco(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do banco de dados

        Returns:
            Dicionário com estatísticas
        """
        try:
            total_cadastros = self.session.query(CadastroImobiliario).count()
            total_proprietarios = self.session.query(Proprietario).count()
            total_enderecos = self.session.query(Endereco).count()
            total_zoneamentos = self.session.query(Zoneamento).count()

            return {
                'total_cadastros': total_cadastros,
                'total_proprietarios': total_proprietarios,
                'total_enderecos': total_enderecos,
                'total_zoneamentos': total_zoneamentos
            }

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao obter estatísticas: {e}")
            return {}

    def registrar_processamento(self, log_data: Dict[str, Any]) -> Optional[int]:
        """
        Registra log de processamento

        Args:
            log_data: Dados do log de processamento

        Returns:
            ID do log criado
        """
        try:
            log = ProcessamentoLog(**log_data)
            self.session.add(log)
            self.session.flush()
            return log.id

        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao registrar log: {e}")
            return None

    def _parse_float(self, valor: Any) -> Optional[float]:
        """
        Converte valor para float de forma segura

        Args:
            valor: Valor a ser convertido

        Returns:
            Float convertido ou None
        """
        if valor is None:
            return None

        if isinstance(valor, (int, float)):
            return float(valor)

        if isinstance(valor, str):
            try:
                return float(valor.replace(',', '.'))
            except ValueError:
                return None

        return None
