# api/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AUTH_SERVICE_DB_HOST: str
    AUTH_SERVICE_DB_NAME: str
    AUTH_SERVICE_DB_USER: str
    AUTH_SERVICE_DB_PASSWORD: str
    AUTH_SERVICE_DB_PORT: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
