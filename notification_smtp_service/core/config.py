import logging
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


logging.basicConfig(level=logging.INFO)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="allow")

    notification_secret_key: str = Field(..., alias="NOTIFICATION_API_SECRET_KEY")
    notification_service_host: str = Field(..., alias="NOTIFICATION_SERVICE_HOST")
    notification_broker_host: str = Field(..., alias="NOTIFICATION_BROKER_HOST")
    notification_broker_port: int = Field(..., alias="NOTIFICATION_BROKER_PORT")
    notification_broker_username: str = Field(..., alias="NOTIFICATION_BROKER_USERNAME")
    notification_broker_password: str = Field(..., alias="NOTIFICATION_BROKER_PASSWORD")
    queue_for_smtp: str = Field(..., alias="QUEUE_FOR_SMTP")
    auth_service_host: str = Field(..., alias="AUTH_SERVICE_HOST")
    auth_service_port: int = Field(..., alias="AUTH_SERVICE_PORT")
    auth_secret_key: str = Field(..., alias="INTERNAL_AUTH_SECRET_KEY")
    smtp_service_host: str = Field(..., alias="SMTP_SERVICE_HOST")
    smtp_service_port: int = Field(..., alias="SMTP_SERVICE_PORT")
    smtp_default_sender: str = Field(..., alias="SMTP_DEFAULT_SENDER")
    smtp_queue_reconnection_period: int = Field(..., alias="SMTP_BROKER_RECONNECTION_PERIOD_SECONDS")
    dlq_ending: str = Field(".dlq", alias="DLQ_ENDING")

    def get_rabbitmq_connection_string(self):
        username = self.notification_broker_username
        password = self.notification_broker_password
        host = self.notification_broker_host
        port = self.notification_broker_port
        return f'amqp://{username}:{password}@{host}/'


settings = Settings()
