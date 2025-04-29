# api/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DB config
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str
    AUTH_SERVICE_DB_SCHEMA: str
    # JWT config
    JWT_AUDIENCE: str
    JWT_ISSUER: str
    JWT_LIFETIME_SECONDS: int
    SECRET_KEY: str

    class Config:
        env_file = "../../../config/.env"

settings = Settings()
