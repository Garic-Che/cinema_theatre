from typing import AsyncGenerator, Optional
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from core.config import settings


# SQLAlchemy Base for models
Base = declarative_base()


class DatabaseManager:
    """Manages async database connections and sessions."""
    
    def __init__(self) -> None:
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        
    def init_db(self) -> None:
        """Initialize the database engine and session factory."""
        
        self.engine = create_async_engine(
            settings.database_dsn,
            echo=False,
            poolclass=NullPool,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    
    async def connect(self) -> None:
        """Connect to the database."""
        if self.engine is None:
            self.init_db()
    
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        if self.engine:
            await self.engine.dispose()
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        if self.session_factory is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager instance
_database_manager: Optional[DatabaseManager] = None


@lru_cache()
def get_database() -> DatabaseManager:
    """Get the global database manager instance."""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a database session."""
    database = get_database()
    async for session in database.get_session():
        yield session
