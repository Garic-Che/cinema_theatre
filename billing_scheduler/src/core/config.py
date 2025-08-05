import os
from logging import config as logging_config

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.logger import LOGGING


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )
    # Настройки для проверки срока действия подписки
    subscription_soon_expiration_days: int = Field(
        7, alias="SUBSCRIPTION_SOON_EXPIRATION_DAYS"
    )
    transaction_timeout_minutes: int = Field(
        10, alias="TRANSACTION_TIMEOUT_MINUTES"
    )

    # Настройки Postgres
    pg_host: str = Field(..., alias="BILLING_DB_HOST")
    pg_port: int = Field(..., alias="BILLING_DB_PORT")
    pg_user: str = Field(..., alias="BILLING_DB_USER")
    pg_password: str = Field(..., alias="BILLING_DB_PASSWORD")
    pg_db: str = Field(..., alias="BILLING_DB_NAME")

    # Настройки Redis
    billing_notification_redis_host: str = Field(
        ..., alias="BILLING_NOTIFICATION_REDIS_HOST"
    )
    redis_port: int = Field(..., alias="REDIS_PORT")
    billing_notification_redis_db: int = Field(
        0, alias="BILLING_NOTIFICATION_REDIS_DB"
    )

    # Настройки внутренней авторизации
    internal_billing_secret_key: str = Field(
        ..., alias="INTERNAL_BILLING_SECRET_KEY"
    )
    internal_auth_secret_key: str = Field(
        ..., alias="INTERNAL_AUTH_SECRET_KEY"
    )
    notification_api_secret_key: str = Field(
        ..., alias="NOTIFICATION_API_SECRET_KEY"
    )

    # Настройки для отправки уведомлений
    notification_service_host: str = Field(
        ..., alias="NOTIFICATION_SERVICE_HOST"
    )
    notification_service_port: int = Field(
        ..., alias="NOTIFICATION_SERVICE_PORT"
    )
    notification_service_scheme: str = Field(
        "http", alias="NOTIFICATION_SERVICE_SCHEME"
    )

    # Настройки для BillingService
    billing_service_host: str = Field(..., alias="BILLING_SERVICE_HOST")
    billing_service_port: int = Field(..., alias="BILLING_SERVICE_PORT")
    billing_service_scheme: str = Field("http", alias="BILLING_SERVICE_SCHEME")

    # Настройки для AuthService
    auth_service_host: str = Field(..., alias="AUTH_SERVICE_HOST")
    auth_service_port: int = Field(..., alias="AUTH_SERVICE_PORT")
    auth_service_scheme: str = Field("http", alias="AUTH_SERVICE_SCHEME")

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}@"
            f"{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def auth_service_url(self) -> str:
        return f"{self.auth_service_scheme}://{self.auth_service_host}:{self.auth_service_port}"

    @property
    def notification_service_url(self) -> str:
        return f"{self.notification_service_scheme}://{self.notification_service_host}:{self.notification_service_port}"

    @property
    def billing_service_url(self) -> str:
        return f"{self.billing_service_scheme}://{self.billing_service_host}:{self.billing_service_port}"


# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

settings = Settings()
