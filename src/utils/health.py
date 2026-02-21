from fastapi import APIRouter
from sqlalchemy import text
from src.database import engine
from src.services.redis_service import redis_service

health_router = APIRouter()


@health_router.get("/health", tags=["Health"])
async def health_check():
    """
    Infra-aware health check.

    Returns:
    - database status
    - redis status

    Always returns HTTP 200 for Docker healthcheck compatibility.
    """

    db_status = "down"
    redis_status = "down"

    # Check database connectivity
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:
        db_status = "down"

    # Check Redis connectivity
    try:
        if redis_service.ping():
            redis_status = "up"
    except Exception:
        redis_status = "down"

    overall_status = "ok" if db_status == "up" and redis_status == "up" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "redis": redis_status,
    }
