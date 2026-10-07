from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.core.database import check_db_connection
from backend.app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health():
    """
    Healthcheck endpoint to verify API and database liveness.
    Does not require Telegram authentication.
    """
    is_db_connected = await check_db_connection()
    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        database="connected" if is_db_connected else "disconnected",
    )
