import os
from logging import config as logging_config

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.logger import LOGGING


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

    # Название проекта. Используется в Swagger-документации
    billing_project_name: str = "Billing-API"
    billing_project_description: str = "API для работы с платежами и возвратами"
    billing_project_version: str = "1.0.0"

    # Настройки Postgres
    pg_host: str = Field(..., alias="BILLING_DB_HOST")
    pg_port: int = Field(..., alias="BILLING_DB_PORT")
    pg_user: str = Field(..., alias="BILLING_DB_USER")
    pg_password: str = Field(..., alias="BILLING_DB_PASSWORD")
    pg_db: str = Field(..., alias="BILLING_DB_NAME")

    # Настройки внутренней авторизации
    internal_billing_secret_key: str = Field(..., alias="INTERNAL_BILLING_SECRET_KEY")

    # YoKassa
    account_id: str = Field(..., alias="YOOKASSA_ACCOUNT_ID")
    secret_key: str = Field(..., alias="YOOKASSA_SECRET_KEY")
    yookassa_api_base: str = Field(..., alias="YOOKASSA_API_BASE")

    billing_host: str = Field(..., alias="BILLING_SERVICE_HOST")
    billing_port: int = Field(..., alias="BILLING_SERVICE_PORT")

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}@"
            f"{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )
    
    @property
    def billing_url_base(self) -> str:
        return f"http://{self.billing_host}:{self.billing_port}"

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

settings = Settings()
