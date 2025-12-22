"""
Health Check Endpoint

Provides system health status for monitoring and debugging.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.schemas.common import HealthCheckResponse
from app.config import get_settings


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the health status of the API and its dependencies",
    tags=["System"]
)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns:
        HealthCheckResponse: System health status
    """
    settings = get_settings()

    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        version=settings.app_version,
        database=db_status,
        timestamp=datetime.utcnow().isoformat(),
    )
