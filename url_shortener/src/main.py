from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.security import APIKeyHeader

from core.config import settings
from core.database import get_database
from api.v1.link import router
from api.v1.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown events."""
    
    # Initialize database
    database = get_database()
    await database.connect()
    
    yield
    
    # Cleanup
    await database.disconnect()


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Url-Shortener",
        description="Microservice for shortening urls",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(router, prefix="/api/v1")
    app.include_router(health_router, prefix="/health")

    api_key_header = APIKeyHeader(name="X-Internal-Auth", auto_error=False)

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
