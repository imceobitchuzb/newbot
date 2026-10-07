from typing import Any, Dict, Optional
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import (
    validate_telegram_init_data,
    TelegramAuthError,
)


class TelegramUserData(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = "en"
    photo_url: Optional[str] = None
    allows_write_to_pm: Optional[bool] = None


class TelegramAuthService:
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN

    def authenticate_init_data(
        self,
        init_data: str,
        max_age_seconds: int = 86400,
    ) -> TelegramUserData:
        """
        Validates initData and extracts strongly-typed Telegram user information.
        """
        validated_data = validate_telegram_init_data(
            init_data_raw=init_data,
            bot_token=self.bot_token,
            max_age_seconds=max_age_seconds,
        )

        user_info = validated_data.get("user_data")
        if not user_info:
            raise TelegramAuthError("initData does not contain a valid user object.")

        return TelegramUserData(
            id=int(user_info["id"]),
            first_name=user_info.get("first_name", ""),
            last_name=user_info.get("last_name"),
            username=user_info.get("username"),
            language_code=user_info.get("language_code", "en"),
            photo_url=user_info.get("photo_url"),
            allows_write_to_pm=user_info.get("allows_write_to_pm"),
        )


telegram_auth_service = TelegramAuthService()
