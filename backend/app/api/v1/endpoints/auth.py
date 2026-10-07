from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.core.security import (
    AuthDateExpiredError,
    InvalidSignatureError,
    MalformedInitDataError,
    TelegramAuthError,
    create_access_token,
)
from backend.app.schemas.auth import AuthResponse, DevAuthRequest, TelegramAuthRequest
from backend.app.schemas.user import UserResponse
from backend.app.services.telegram_auth import TelegramUserData, telegram_auth_service
from backend.app.services.user_service import user_service

router = APIRouter()


@router.post(
    "/telegram",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate via Telegram WebApp initData",
)
async def auth_telegram(
    payload: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validates Telegram WebApp initData HMAC-SHA256 signature and authenticates the student.
    Creates a new user profile on first launch or refreshes existing user session.
    Returns a secure JWT Bearer token for application requests.
    """
    try:
        tg_user_data = telegram_auth_service.authenticate_init_data(payload.init_data)
    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram signature.",
        )
    except AuthDateExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram authentication expired.",
        )
    except MalformedInitDataError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed Telegram initData: {str(e)}",
        )
    except TelegramAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Telegram authentication failed: {str(e)}",
        )

    user = await user_service.get_or_create_from_telegram(db, tg_user_data)
    access_token = create_access_token(user_id=str(user.id))

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/dev",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate authentication for local browser development",
)
async def auth_dev(
    payload: DevAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Development-only simulated authentication for testing in desktop browsers outside Telegram.
    Disabled in production mode.
    """
    if settings.APP_ENV == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development login is disabled in production.",
        )

    dev_tg_user = TelegramUserData(
        id=payload.telegram_id or 12345678,
        first_name=payload.first_name or "Dev Student",
        username=payload.username or "dev_student",
        language_code="en",
    )

    user = await user_service.get_or_create_from_telegram(db, dev_tg_user)
    access_token = create_access_token(user_id=str(user.id))

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
