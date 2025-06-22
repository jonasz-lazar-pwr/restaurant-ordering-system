# === api/core/config.py ===

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # RabbitMQ
    RABBITMQ_URL: str
    PAYMENT_QUEUE: str
    ORDER_QUEUE: str
    STAFF_QUEUE: str
    NOTIFICATION_QUEUE: str

    # PayU
    # Change ID, POS_ID and SECRET after switching to proper shop
    # Optional PayU settings – will use default hardcoded values if .env is not present
    PAYU_CLIENT_ID: str = "490096"
    PAYU_CLIENT_SECRET: str = "585ec418430275c1252a591b7ef07185"
    PAYU_MERCHANT_POS_ID: str = "490096"
    PAYU_SANDBOX_URL: str = "https://secure.snd.payu.com/"

    CORS_ALLOW_ORIGINS: str

    # DB settings
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str
    PAYMENT_SERVICE_DB_SCHEMA: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore"
    )

settings = Settings()
