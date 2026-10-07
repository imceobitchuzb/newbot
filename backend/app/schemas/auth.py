from typing import Optional
from pydantic import BaseModel, Field
from backend.app.schemas.user import UserResponse


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(..., min_length=1, description="Raw Telegram WebApp initData string")


class DevAuthRequest(BaseModel):
    telegram_id: Optional[int] = Field(default=12345678, description="Simulated Telegram ID for local testing")
    first_name: Optional[str] = Field(default="Dev", description="Simulated First Name")
    username: Optional[str] = Field(default="dev_student", description="Simulated Username")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
