import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserProfileBase(BaseModel):
    target_score: int = 1400
    diagnostic_status: str = "not_started"
    study_goal: str = "Score 1400+ in 4 months"
    daily_goal_minutes: int = 30
    math_estimate: Optional[int] = None
    rw_estimate: Optional[int] = None


class UserProfileUpdate(BaseModel):
    target_score: Optional[int] = None
    diagnostic_status: Optional[str] = None
    study_goal: Optional[str] = None
    daily_goal_minutes: Optional[int] = None


class UserProfileResponse(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
