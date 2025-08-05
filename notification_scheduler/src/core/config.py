from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional, List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # Project metadata
    PROJECT_NAME: str = "Movie theater"
    PROJECT_DESCRIPTION: str = "The best movie theater for everyone"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"

    # Debug mode
    DEBUG: bool = True

    # Secret keys for cryptographic operations
    SECRET_KEY: SecretStr
    INTERNAL_AUTH_SECRET_KEY: SecretStr
    NOTIFICATION_API_SECRET_KEY: SecretStr

    # Database configuration (PostgreSQL for notifications)
    NOTIFICATION_DB_HOST: str = "notification-db"
    NOTIFICATION_DB_PORT: int = 5436
    NOTIFICATION_DB_NAME: str = "notification_db"
    NOTIFICATION_DB_USER: str = "admin"
    NOTIFICATION_DB_PASSWORD: SecretStr

    DATABASE_TYPE: str = "postgres"

    @property
    def database_dsn(self) -> str:
        """
        Construct the async PostgreSQL DSN for SQLAlchemy.
        """
        return (
            f"postgresql+asyncpg://{self.NOTIFICATION_DB_USER}:"
            f"{self.NOTIFICATION_DB_PASSWORD.get_secret_value()}@{self.NOTIFICATION_DB_HOST}:"
            f"{self.NOTIFICATION_DB_PORT}/{self.NOTIFICATION_DB_NAME}"
        )

    # Auth service configuration
    AUTH_SERVICE_HOST: str = "auth_service"
    AUTH_SERVICE_PORT: int = 8000

    @property
    def auth_host(self) -> str:
        """
        Construct the auth service URL.
        """
        return f"http://{self.AUTH_SERVICE_HOST}:{self.AUTH_SERVICE_PORT}"

    # UGC CRUD service configuration
    UGC_CRUD_SERVICE_HOST: str = "ugc_crud_service"
    UGC_CRUD_SERVICE_PORT: int = 8000

    @property
    def ugc_crud_host(self) -> str:
        """
        Construct the UGC CRUD service URL.
        """
        return f"http://{self.UGC_CRUD_SERVICE_HOST}:{self.UGC_CRUD_SERVICE_PORT}"

    # Notification service configuration
    NOTIFICATION_SERVICE_HOST: str = "notification-service"
    NOTIFICATION_SERVICE_PORT: int = 8000

    @property
    def notification_host(self) -> str:
        """
        Construct the notification service URL.
        """
        return f"http://{self.NOTIFICATION_SERVICE_HOST}:{self.NOTIFICATION_SERVICE_PORT}"

    # Theatre service configuration
    THEATRE_SERVICE_HOST: str = "theatre_service"
    THEATRE_SERVICE_PORT: int = 8000

    @property
    def theatre_host(self) -> str:
        """
        Construct the theatre service URL.
        """
        return f"http://{self.THEATRE_SERVICE_HOST}:{self.THEATRE_SERVICE_PORT}"

    # Scheduler configuration
    SCHEDULER_INTERVAL: int = 60  # Seconds between scheduler runs
    MAX_NOTIFICATIONS_PER_USER: int = 5  # Max notifications per user
    MAX_CONCURRENT_REQUESTS: int = 10  # Max concurrent API requests

    # API retry configuration
    API_RETRY_ATTEMPTS: int = 3
    API_RETRY_DELAY: float = 1.0
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0

    # API timeout configuration
    API_TIMEOUT: float = 30.0

    # Notification content limits
    MAX_NOTIFICATION_ITEMS: int = 5

    # Sentry configuration
    SENTRY_DSN_NOTIFICATION: Optional[str] = None

    INTERNAL_AUTH_SECRET_KEY: str = "INTERNAL_AUTH_SECRET_KEY"

    UGC_CRUD_API_SECRET_KEY: str = "UGC_CRUD_API_SECRET_KEY"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Instantiate settings
settings = Settings()