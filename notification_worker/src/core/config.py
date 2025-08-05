import os
from logging import config as logging_config
from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"), env_file_encoding="utf-8"
    )
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

    @property
    def notification_broker_url(self) -> str:
        return f"amqp://{self.notification_broker_username}:{self.notification_broker_password}@{self.notification_broker_host}:{self.notification_broker_port}/"

    # Настройки очередей
    queue_for_worker: str = Field(..., alias="QUEUE_FOR_WORKER")
    queue_for_smtp: str = Field(..., alias="QUEUE_FOR_SMTP")
    queue_for_websocket: str = Field(..., alias="QUEUE_FOR_WEBSOCKET")
    dlq_ending: str = Field(".dlq", alias="DLQ_ENDING")


settings = Settings()
