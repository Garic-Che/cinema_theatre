import os
from logging import config as logging_config
from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )
    notification_project_name: str = "API нотификаций"
    notification_project_description: str = "Приём нотификаций"
    notification_project_version: str = "1.0.0"

    # Настройки базы данных
    notification_db_host: str = Field(..., alias="NOTIFICATION_DB_HOST")
    notification_db_port: int = Field(..., alias="NOTIFICATION_DB_PORT")
    notification_db_name: str = Field(..., alias="NOTIFICATION_DB_NAME")
    notification_db_user: str = Field(..., alias="NOTIFICATION_DB_USER")
    notification_db_password: str = Field(
        ..., alias="NOTIFICATION_DB_PASSWORD"
    )

    # Настройки брокера
    notification_broker_host: str = Field(
        ..., alias="NOTIFICATION_BROKER_HOST"
    )
    notification_broker_port: int = Field(
        ..., alias="NOTIFICATION_BROKER_PORT"
    )
    notification_broker_username: str = Field(
        ..., alias="NOTIFICATION_BROKER_USERNAME"
    )
    notification_broker_password: str = Field(
        ..., alias="NOTIFICATION_BROKER_PASSWORD"
    )
    queue_for_worker: str = Field(..., alias="QUEUE_FOR_WORKER")
    dlq_ending: str = Field(".dlq", alias="DLQ_ENDING")

    # auth-server
    auth_service_schema: str = "http://"
    auth_service_host: str = Field("auth_service", alias="AUTH_SERVICE_HOST")
    auth_service_port: int = Field(8000, alias="AUTH_SERVICE_PORT")
    jwt_secret_key: str = Field(..., alias="AUTH_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")

    # Sentry configuration
    sentry_dsn_notification: str = Field(..., alias="SENTRY_DSN_NOTIFICATION")

    # Аутентификация для внутренних сервисов
    notification_api_secret_key: str = Field(
        ..., alias="NOTIFICATION_API_SECRET_KEY"
    )


# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

settings = Settings()
