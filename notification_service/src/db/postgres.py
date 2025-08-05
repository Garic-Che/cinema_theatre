from core.config import settings
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

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


# Функция понадобится при внедрении зависимостей
# Dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    logger.info("Initializing database session")
    async with async_session() as session:
        try:
            logger.info("Database session created successfully")
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            logger.info("Closing database session")
            await session.close()
