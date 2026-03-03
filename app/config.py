import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "903e4eaee43e18b9252eecf0738645bd40df9d2b5e5892451acc718438d76a58")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2880

    DB_USER: str = os.getenv("DB_USER", "arshad")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "KldkhhmS%23392")
    DB_HOST: str = os.getenv("DB_HOST", "159.223.92.152")
    DB_NAME: str = os.getenv("DB_NAME", "auth_service_refund")
    DB_PORT: str = os.getenv("DB_PORT", "3306")

    KAFKA_BROKER_URL: str = os.getenv("KAFKA_BROKER_URL", "kafka:9092")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC", "auth_logging")
    KAFKA_USERNAME: str = os.getenv("KAFKA_USERNAME", "arshad")
    KAFKA_PASSWORD: str = os.getenv("KAFKA_PASSWORD", "KldkhhmS392")
    KAFKA_COUNT_TOPIC: str = os.getenv("KAFKA_COUNT_TOPIC", "api_count")
    KAFKA_APP_ERROR_TOPIC: str = os.getenv("KAFKA_APP_ERROR_TOPIC", "app_error")
    
    class Config:
        env_file = ".env"

settings = Settings()
