from core.config import settings
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Создаём базовый класс для будущих моделей
Base = declarative_base()
# Создаём движок
dsn = (
    f"postgresql+asyncpg://{settings.notification_db_user}:{settings.notification_db_password}@"
    f"{settings.notification_db_host}:{settings.notification_db_port}/{settings.notification_db_name}"
)
engine = create_async_engine(dsn, echo=True, future=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
