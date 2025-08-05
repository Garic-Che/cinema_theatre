from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DEBUG: bool = True

    # Database configuration
    SHORTENER_DB_HOST: str = "url-shortener-db"
    SHORTENER_DB_PORT: int = 5436
    SHORTENER_DB_NAME: str = "url-shortener-db"
    SHORTENER_DB_USER: str = "admin"
    SHORTENER_DB_PASSWORD: SecretStr

    SHORTENER_SERVICE_HOST: str = "url-shortener"
    SHORTENER_SERVICE_PORT: int = 8000

    LINK_EXPIRY_PERIOD_IN_DAYS: int = 2
    DATABASE_TYPE: str = "postgres"

    ALLOWED_HOSTS_TO_SHORTEN: str

    URL_SHORTENER_API_SECRET_KEY: str
    

    @property
    def database_dsn(self) -> str:
        """
        Construct the async PostgreSQL DSN for SQLAlchemy.
        """
        return (
            f"postgresql+asyncpg://{self.SHORTENER_DB_USER}:"
            f"{self.SHORTENER_DB_PASSWORD.get_secret_value()}@{self.SHORTENER_DB_HOST}:"
            f"{self.SHORTENER_DB_PORT}/{self.SHORTENER_DB_NAME}"
        )
    
    @property
    def url_shortener_base_url(self) -> str:
        return f"http://{self.SHORTENER_SERVICE_HOST}:{self.SHORTENER_SERVICE_PORT}/api/v1"
    
    @property
    def hosts_allowed_to_shorten(self) -> str:
        return self.ALLOWED_HOSTS_TO_SHORTEN.split(',')

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    


# Instantiate settings
settings = Settings()