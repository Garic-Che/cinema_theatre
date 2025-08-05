from datetime import datetime, timezone

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="allow"
    )

    shortener_db_host: str = Field(..., alias="SHORTENER_DB_HOST")
    shortener_db_port: int = Field(..., alias="SHORTENER_DB_PORT")
    shortener_db_name: str = Field(..., alias="SHORTENER_DB_NAME")
    shortener_db_user: str = Field(..., alias="SHORTENER_DB_USER")
    shortener_db_password: str = Field(..., alias="SHORTENER_DB_PASSWORD")

    shortener_service_host: str = Field(..., alias="SHORTENER_SERVICE_HOST")
    shortener_service_port: int = Field(..., alias="SHORTENER_SERVICE_PORT")
    shortener_service_secret: str = Field(..., alias="URL_SHORTENER_API_SECRET_KEY")

    @property
    def postgres_dsn(self):
        return (
            f"postgresql+asyncpg://"
            f"{self.shortener_db_user}:{self.shortener_db_password}"
            f"@{self.shortener_db_host}/{self.shortener_db_name}"
        )
    
    @property
    def base_api_url(self):
        return f"http://{self.shortener_service_host}:{self.shortener_service_port}/api/v1"
    

settings = Settings()
