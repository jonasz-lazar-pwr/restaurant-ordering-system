# === api/core/config.py ===

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # RabbitMQ
    RABBITMQ_URL: str
    PAYMENT_QUEUE: str

    # PayU
    # Change ID, POS_ID and SECRET after switching to proper shop
    PAYU_CLIENT_ID = "490096"
    PAYU_CLIENT_SECRET = "585ec418430275c1252a591b7ef07185"
    PAYU_MERCHANT_POS_ID = "490096"
    PAYU_SANDBOX_URL = "https://secure.snd.payu.com/"

    CORS_ALLOW_ORIGINS: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = 'utf-8',
        extra = 'ignore'
    )

settings = Settings()
