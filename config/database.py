"""
Database Configuration - Configurações de conexão com PostgreSQL
Centraliza todas as configurações de banco de dados
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Configurações do PostgreSQL"""
    host: str
    port: int
    database: str
    username: str
    password: str
    schema: str = "public"

    @property
    def connection_string(self) -> str:
        """Retorna string de conexão PostgreSQL"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_connection_string(self) -> str:
        """Retorna string de conexão PostgreSQL assíncrona"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseSettings:
    """Gerenciador de configurações de banco de dados"""

    def __init__(self):
        self._load_database_config()

    def _load_database_config(self):
        """Carrega configurações do banco de dados"""
        self.database = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'cadastros_imobiliarios'),
            username=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            schema=os.getenv('DB_SCHEMA', 'public')
        )

    def get_database_config(self) -> DatabaseConfig:
        """Retorna configurações do banco de dados"""
        return self.database


# Instância global
db_settings = DatabaseSettings()
