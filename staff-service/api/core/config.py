# api/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database settings
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str
    STAFF_SERVICE_DB_SCHEMA: str

    # RabbitMQ settings
    RABBITMQ_URL: str
    ORDER_QUEUE: str
    STAFF_QUEUE: str
    PAYMENT_QUEUE: str
    NOTIFICATION_QUEUE: str

    # JWT settings
    JWT_AUDIENCE: str
    JWT_ISSUER: str
    JWT_SECRET_KEY: str

    # Other settings
    CORS_ALLOW_ORIGINS: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = 'utf-8',
        extra = 'ignore'
    )

settings = Settings()
