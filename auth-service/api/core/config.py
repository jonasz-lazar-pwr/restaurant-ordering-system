# api/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str
    AUTH_SERVICE_DB_SCHEMA: str

    JWT_AUDIENCE: str
    JWT_ISSUER: str
    JWT_LIFETIME_SECONDS: int
    SECRET_KEY: str

    CORS_ALLOW_ORIGINS: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = 'utf-8',
        extra = 'ignore'
    )

settings = Settings()
