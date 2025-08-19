"""
Cadastro Service - Serviço de alto nível para extração de cadastros imobiliários
Agora orquestra TODAS as requisições e salva JSONs por módulo.
"""

from typing import Dict, List, Any, Optional, Union
import logging
import time
from datetime import datetime

from service.soap_client import CadastralSOAPClient, SOAPClientError
from service.cache_service import CacheService
from service.storage_service import FileStorageService
from service.statistics_service import StatisticsService
from interface.cli_interface import CLIInterface, ProgressTracker
from config.settings import settings


class CadastroService:
    """
    Serviço orquestrador para extração completa de cadastros imobiliários
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.soap_client = CadastralSOAPClient()
        self.cache_service = CacheService()
        self.file_storage_service = FileStorageService()
        self.stats = StatisticsService()
        self.app_config = settings.app
        # Defaults defensivos
        self.request_delay = float(getattr(self.app_config, "request_delay", 0.0))
        self.save_interval = int(getattr(self.app_config, "save_interval", 250))

    # ------------------- Pipeline principal -------------------
    def extrair_completo(self) -> Dict[str, str]:
        """
        Extrai cadastros e TODOS os módulos relacionados e salva em JSONs separados.
        Retorna { nome_arquivo: caminho }.
        """
        inicio = datetime.now()

        # 1) Buscar cadastros (geral) – tenta sem filtros e cai para combinações comuns
        CLIInterface.mostrar_info("Buscando cadastros (geral)...")
        cadastros = self._buscar_cadastros_geral()
        CLIInterface.mostrar_sucesso(f"Total de cadastros: {len(cadastros)}")

        if not cadastros:
            CLIInterface.mostrar_aviso("Nenhum cadastro retornado pela API.")
            # mesmo assim vamos salvar JSONs vazios para manter o fluxo
            return self.file_storage_service.salvar_varios_datasets(
                {
                    "cadastros": [],
                    "enderecos": [],
                    "proprietarios": [],
                    "testadas": [],
                    "subreceitas": [],
                    "zoneamento": [],
                    "anexos": [],
                    "historico": [],
                    "bci": [],
                    "itbi": [],
                }
            )

        # Acumuladores por módulo
        enderecos: List[Dict[str, Any]] = []
        proprietarios: List[Dict[str, Any]] = []
        testadas: List[Dict[str, Any]] = []
        subreceitas: List[Dict[str, Any]] = []
        zoneamentos: List[Dict[str, Any]] = []
        anexos: List[Dict[str, Any]] = []
        historicos: List[Dict[str, Any]] = []
        bloco_itens: List[Dict[str, Any]] = []
        itbis: List[Dict[str, Any]] = []

        tracker = ProgressTracker(total=len(cadastros))
        for idx, cad in enumerate(cadastros, start=1):
            codigo = str(cad.get("codigo_cadastro") or cad.get("codigo", "")).strip()
            tracker.atualizar(idx, extra=f"cadastro {codigo or 'N/D'}")

            if not codigo:
                continue

            # 2) Chamadas por cadastro (cada módulo com try/catch isolado)
            try:
                enderecos += self._tag(
                    self.soap_client.buscar_enderecos(codigo), codigo, "codigo_cadastro"
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] enderecos: {e}")

            try:
                proprietarios += self._tag(
                    self.soap_client.buscar_proprietarios(codigo),
                    codigo,
                    "codigo_cadastro",
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] proprietarios: {e}")

            try:
                testadas += self._tag(
                    self.soap_client.buscar_testadas(codigo), codigo, "codigo_cadastro"
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] testadas: {e}")

            try:
                subreceitas += self._tag(
                    self.soap_client.buscar_subreceitas(codigo),
                    codigo,
                    "codigo_cadastro",
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] subreceitas: {e}")

            try:
                zoneamentos += self._tag(
                    self.soap_client.buscar_zoneamentos(codigo),
                    codigo,
                    "codigo_cadastro",
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] zoneamento: {e}")

            # Novos módulos
            try:
                anexos += self._tag(
                    self.soap_client.buscar_anexos(codigo), codigo, "codigo_cadastro"
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] anexos: {e}")

            try:
                historicos += self._tag(
                    self.soap_client.buscar_historico(codigo), codigo, "codigo_cadastro"
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] historico: {e}")

            try:
                bloco_itens += self._tag(
                    self.soap_client.buscar_bloco_itens(codigo),
                    codigo,
                    "codigo_cadastro",
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] bloco_itens (BCI): {e}")

            try:
                itbis += self._tag(
                    self.soap_client.buscar_itbi(codigo), codigo, "codigo_cadastro"
                )
            except Exception as e:
                self.logger.warning(f"[{codigo}] itbi: {e}")

            # Salvamento parcial (opcional)
            if self.save_interval and (idx % self.save_interval == 0):
                self.file_storage_service.salvar_progresso_parcial(
                    cadastros[:idx], sufixo="auto"
                )

            # Pequeno delay entre cadastros (se configurado)
            if self.request_delay and (idx < len(cadastros)):
                time.sleep(self.request_delay)

        # 3) Salvar tudo em arquivos separados
        CLIInterface.mostrar_info("Salvando JSONs por módulo...")
        resultados = self.file_storage_service.salvar_varios_datasets(
            {
                "cadastros": cadastros,
                "enderecos": enderecos,
                "proprietarios": proprietarios,
                "testadas": testadas,
                "subreceitas": subreceitas,
                "zoneamento": zoneamentos,
                "anexos": anexos,
                "historico": historicos,
                "bci": bloco_itens,  # buscaBlocoItens
                "itbi": itbis,  # buscaItbiCadastroImobiliario
            }
        )

        dur = (datetime.now() - inicio).total_seconds()
        CLIInterface.mostrar_sucesso(f"Extração finalizada em {dur:.1f}s.")
        return {k: v or "" for k, v in resultados.items()}

    # ------------------- Helpers -------------------
    def _buscar_cadastros_geral(self) -> List[Dict[str, Any]]:
        """
        Busca cadastros tentando combinações comuns de filtros.
        1) Sem filtros (mais amplo)
        2) tipo_consulta=1, situacao=1
        3) tipo_consulta=2, situacao=1
        4) tipo_consulta=1 (sem situacao)
        5) situacao=1 (sem tipo_consulta)
        """
        tentativas = [
            {},  # sem filtros
            {"tipo_consulta": 1, "situacao": 1},
            {"tipo_consulta": 2, "situacao": 1},
            {"tipo_consulta": 1},
            {"situacao": 1},
        ]

        for params in tentativas:
            try:
                lista = self.soap_client.buscar_cadastro_geral(**params)
                normalizados: List[Dict[str, Any]] = []
                for c in lista:
                    if not isinstance(c, dict):
                        continue
                    c2 = dict(c)
                    if "codigo" in c2 and "codigo_cadastro" not in c2:
                        c2["codigo_cadastro"] = c2["codigo"]
                    normalizados.append(c2)

                if normalizados:
                    return normalizados

            except SOAPClientError as e:
                CLIInterface.mostrar_erro(f"Erro ao buscar cadastros com {params}: {e}")
                # tenta próxima combinação
            except Exception as e:
                self.logger.warning(f"Falha em buscar cadastros com {params}: {e}")
                # tenta próxima combinação

        # se nada retornou, devolve lista vazia
        return []

    @staticmethod
    def _tag(
        items: Union[List[Dict[str, Any]], Dict[str, Any], None],
        codigo: str,
        campo: str,
    ) -> List[Dict[str, Any]]:
        """
        Garante que cada item carregue o código do cadastro para vínculo.
        """
        if items is None:
            return []
        if isinstance(items, dict):
            items = [items]
        out: List[Dict[str, Any]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            it2 = dict(it)
            it2.setdefault(campo, codigo)
            out.append(it2)
        return out
