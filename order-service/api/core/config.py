# api/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DB config
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str
    ORDER_SERVICE_DB_SCHEMA: str

    # JWT config
    SECRET_KEY: str
    JWT_ISSUER: str

    class Config:
        env_file = "../../../config/.env"

settings = Settings()
