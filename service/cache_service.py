"""
Cache Service - Gerencia o armazenamento e recuperação de cadastros no cache local
"""

import os
import json
from typing import List, Dict, Optional

class CacheService:
    """
    Serviço de cache para cadastros imobiliários
    """

    CACHE_DIR = "data/cache"

    def __init__(self):
        """Inicializa o serviço de cache"""
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def salvar_cache(self, codigo_intervalo: str, cadastros: List[Dict]) -> None:
        """
        Salva cadastros no cache local

        Args:
            codigo_intervalo: Intervalo de códigos (ex: "1-100")
            cadastros: Lista de cadastros a serem salvos
        """
        arquivo_cache = os.path.join(self.CACHE_DIR, f"cache_{codigo_intervalo}.json")
        try:
            with open(arquivo_cache, 'w', encoding='utf-8') as f:
                json.dump(cadastros, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar cache para o intervalo {codigo_intervalo}: {e}")

    def carregar_cache(self, codigo_intervalo: str) -> Optional[List[Dict]]:
        """
        Carrega cadastros do cache local

        Args:
            codigo_intervalo: Intervalo de códigos (ex: "1-100")

        Returns:
            Lista de cadastros ou None se o cache não existir
        """
        arquivo_cache = os.path.join(self.CACHE_DIR, f"cache_{codigo_intervalo}.json")
        if not os.path.exists(arquivo_cache):
            return None

        try:
            with open(arquivo_cache, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar cache para o intervalo {codigo_intervalo}: {e}")
            return None

    def limpar_cache(self) -> None:
        """
        Limpa todos os arquivos de cache
        """
        try:
            for arquivo in os.listdir(self.CACHE_DIR):
                caminho_arquivo = os.path.join(self.CACHE_DIR, arquivo)
                if os.path.isfile(caminho_arquivo):
                    os.remove(caminho_arquivo)
        except Exception as e:
            print(f"Erro ao limpar cache: {e}")
