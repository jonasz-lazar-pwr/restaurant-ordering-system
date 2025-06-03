# api/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    AUTH_SERVICE_HOST: str = "auth-service"
    AUTH_SERVICE_PORT: int

    ORDER_SERVICE_HOST: str = "order-service"
    ORDER_SERVICE_PORT: int

    PAYMENT_SERVICE_HOST: str = "payment-service"
    PAYMENT_SERVICE_PORT: int

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str
    JWT_ISSUER: str

    CORS_ALLOW_ORIGINS: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = 'utf-8',
        extra = 'ignore'
    )

settings = Settings()
