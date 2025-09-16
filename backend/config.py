# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Configurações do banco de dados
    DATABASE_URL: str = "sqlite:///./inventory.db"  # SQLite local
    # Exemplo se usar PostgreSQL:
    # DATABASE_URL: str = "postgresql://user:password@localhost:5432/inventory"

    # Segurança
    SECRET_KEY: str = "supersecret"     # usado para JWT ou encriptação
    AGENT_SECRET: str = "agentsecret"   # chave compartilhada com os agentes

    # Opções adicionais
    DEBUG: bool = True

    class Config:
        env_file = ".env"  # permite carregar variáveis de um arquivo .env

# Instância global
settings = Settings()
