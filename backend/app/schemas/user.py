import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    language_code: Optional[str] = "en"
    avatar_url: Optional[str] = None
    target_score: int = 1400


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    target_score: Optional[int] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    current_score_estimate: int
    math_estimate: int
    rw_estimate: int
    level: int
    xp: int
    is_active: bool
    last_active_at: datetime
    created_at: datetime
    updated_at: datetime
