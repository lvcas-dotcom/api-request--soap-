"""
File Storage Service - Gerencia toda a lógica de persistência e salvamento de dados
Responsável por salvar arquivos de progresso, resultados finais e datasets por módulo.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from interface.cli_interface import CLIInterface


class FileStorageService:
    """
    Serviço especializado de salvamento/leituras de arquivos JSON.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or "./data"
        self.data_dir = os.path.join(self.base_dir, "json")
        os.makedirs(self.data_dir, exist_ok=True)

    # ---------------- Cadastros (legado, compat) ----------------
    def salvar_progresso_parcial(
        self, cadastros: List[Dict[str, Any]], sufixo: str = ""
    ) -> Optional[str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sufixo_str = f"_{sufixo}" if sufixo else ""
        arquivo = os.path.join(
            self.data_dir, f"cadastros_progresso_{timestamp}{sufixo_str}.json"
        )
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(cadastros, f, ensure_ascii=False, indent=2)
            CLIInterface.mostrar_aviso(f"Progresso salvo em: {arquivo}")
            return arquivo
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar progresso: {e}")
            return None

    def salvar_resultado_final(
        self,
        cadastros: List[Dict[str, Any]],
        metadados: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo = os.path.join(self.data_dir, f"cadastros_completo_{timestamp}.json")
        try:
            envelope = {
                "meta": {"gerado_em": timestamp, **(metadados or {})},
                "cadastros": cadastros,
            }
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(envelope, f, ensure_ascii=False, indent=2)
            CLIInterface.mostrar_sucesso(f"Resultado final salvo em: {arquivo}")
            return arquivo
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar resultado final: {e}")
            return None

    # ---------------- NOVO: salvar datasets por módulo ----------------
    def salvar_dataset(self, nome: str, dados: List[Dict[str, Any]]) -> Optional[str]:
        """
        Salva um dataset único (lista de dicts) em data/json/{nome}.json
        """
        arquivo = os.path.join(self.data_dir, f"{nome}.json")
        try:
            with open(arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            CLIInterface.mostrar_sucesso(
                f"{nome}.json salvo com {len(dados)} registros."
            )
            return arquivo
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao salvar {nome}.json: {e}")
            return None

    def salvar_varios_datasets(
        self, mapas: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Optional[str]]:
        """
        Recebe um mapa { nome_arquivo: lista_de_dicts } e salva todos.
        Retorna { nome_arquivo: caminho_ou_None }.
        """
        resultados = {}
        for nome, dados in mapas.items():
            resultados[nome] = self.salvar_dataset(nome, dados)
        return resultados

    # ---------------- Utilidades ----------------
    def carregar_dados_salvos(self, caminho_arquivo: str) -> Optional[Dict[str, Any]]:
        try:
            if not os.path.exists(caminho_arquivo):
                return None
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao carregar {caminho_arquivo}: {e}")
            return None

    def listar_arquivos_salvos(self, tipo="todos"):
        try:
            arquivos = []
            for arquivo in os.listdir(self.data_dir):
                if tipo == "todos":
                    if arquivo.endswith(".json"):
                        arquivos.append(os.path.join(self.data_dir, arquivo))
                elif tipo == "progresso":
                    if arquivo.startswith("cadastros_progresso_"):
                        arquivos.append(os.path.join(self.data_dir, arquivo))
                elif tipo == "completo":
                    if arquivo.startswith("cadastros_completo_"):
                        arquivos.append(os.path.join(self.data_dir, arquivo))
            return sorted(arquivos)
        except Exception as e:
            CLIInterface.mostrar_erro(f"Erro ao listar arquivos: {e}")
            return []
