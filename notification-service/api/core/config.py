# api/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database settings
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str
    NOTIFICATION_SERVICE_DB_SCHEMA: str

    # === AWS config ===
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_SESSION_TOKEN: str

    AWS_REGION: str
    AWS_SNS_TOPIC_ARN: str
    DEFAULT_NOTIFICATION_EMAIL: str

    # RabbitMQ settings
    RABBITMQ_URL: str
    ORDER_QUEUE: str
    STAFF_QUEUE: str
    PAYMENT_QUEUE: str
    NOTIFICATION_QUEUE: str

    # === Other config ===
    CORS_ALLOW_ORIGINS: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow"
    )

settings = Settings()
