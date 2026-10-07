from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.database import check_db_connection
from backend.app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health():
    """
    Readiness check endpoint to verify API and database liveness.
    Returns 503 Service Unavailable if database is unreachable.
    Does not require Telegram authentication.
    """
    is_db_connected = await check_db_connection()
    if not is_db_connected:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "app": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "database": "disconnected",
            },
        )

    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        database="connected",
    )
