from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    sns_topic_arn: str

    class Config:
        env_file = "../../../config/.env"

settings = Settings()
