# src/main.py
"""
FastAPI Notification-Scheduler Microservice

This service reads notification schedules from PostgreSQL, gathers data from external APIs,
and triggers personalized notification creation through another microservice.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.v1.health import router
from core.config import settings
from core.database import get_database
from core.logger import setup_logging
from services.scheduler import NotificationScheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown events."""
    
    # Setup logging
    setup_logging(settings)
    logger = logging.getLogger(__name__)
    logger.info("Starting Notification-Scheduler microservice...")
    
    # Initialize database
    database = get_database()
    await database.connect()
    logger.info("Database connected successfully")
    
    # Start the notification scheduler
    scheduler = NotificationScheduler()
    scheduler_task = asyncio.create_task(scheduler.start())
    logger.info("Notification scheduler started")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Notification-Scheduler microservice...")
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    await database.disconnect()
    logger.info("Shutdown complete")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Notification-Scheduler",
        description="Microservice for scheduling and triggering personalized notifications",
        version="1.0.0",
        lifespan=lifespan,
    )


    # Include routers
    app.include_router(router, prefix="/api/v1", tags=["health"])

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )