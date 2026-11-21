"""Configuration lue depuis les variables d'environnement ou le fichier .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://gestquinca:gestquinca_dev@localhost:5432/gestquinca"
    jwt_secret: str = "changez-moi-avant-de-deployer-cle-longue-de-32-caracteres"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:5173"


settings = Settings()
