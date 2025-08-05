from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    protocol: str = Field("http://")
    host: str = ...
    port: int = ...

    def get_host(self):
        return f"{self.protocol}{self.host}:{self.port}"


class CommonSettingsWithPassword(CommonSettings):
    username: str = ...
    password: str = ...


class DBSettings(CommonSettingsWithPassword):
    model_config = SettingsConfigDict(env_prefix="NOTIFICATION_DB_")
    name: str = ...
    protocol: str = Field("postgresql://")
    username: str = Field(..., alias="NOTIFICATION_DB_USER")

    def get_connection_url(self):
        return f"{self.protocol}{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class RabbitMQSettings(CommonSettingsWithPassword):
    model_config = SettingsConfigDict(env_prefix="NOTIFICATION_BROKER_")
    protocol: str = Field("amqp://")

    def get_connection_url(self):
        return f"{self.protocol}{self.username}:{self.password}@{self.host}:{self.port}/"


class ServiceSettings(CommonSettings):
    model_config = SettingsConfigDict(env_prefix="NOTIFICATION_SERVICE_")
    notification_api_secret_key: str = Field(..., alias="NOTIFICATION_API_SECRET_KEY")
