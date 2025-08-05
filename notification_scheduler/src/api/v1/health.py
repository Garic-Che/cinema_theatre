# api/v1/health.py
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for the Notification-Scheduler service.
    Returns basic service information and status.
    """
    return {
        "status": "ok",
        "service": "notification-scheduler",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }

@router.get("/health/db", status_code=status.HTTP_200_OK)
async def db_health_check(session: AsyncSession = Depends(get_db_session)):
    """
    Database health check endpoint.
    Verifies that the service can connect to the database.
    """
    try:
        # Execute a simple query to verify database connection
        result = await session.execute(text("SELECT 1"))
        if result.scalar() == 1:
            return {
                "status": "ok",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            logger.error("Database health check failed: unexpected result")
            return {
                "status": "error",
                "database": "error",
                "message": "Unexpected result from database",
                "timestamp": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "error",
            "database": "disconnected",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
