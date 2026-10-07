from datetime import datetime
from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from backend.app.models.enums import MistakeStatus, MistakeType
from backend.app.schemas.question import QuestionOptionPublic


class MistakeClassifyRequest(BaseModel):
    mistake_type: MistakeType


class MistakeReviewRequest(BaseModel):
    mistake_type: Optional[MistakeType] = None


class MistakeRetryRequest(BaseModel):
    selected_option_id: uuid.UUID
    time_spent_seconds: int = Field(default=0, ge=0, le=3600)


class MistakeRetryResponse(BaseModel):
    is_correct: bool
    selected_option_id: uuid.UUID
    correct_option_id: uuid.UUID
    explanation: str
    hint: Optional[str] = None
    sat_shortcut: Optional[str] = None
    new_status: str
    correct_retry_count: int
    incorrect_retry_count: int
    is_mastered: bool


class MistakeEntryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    question_id: uuid.UUID
    attempt_id: Optional[uuid.UUID] = None
    subject: str
    domain: str
    skill: str
    status: str
    mistake_type: str
    review_count: int
    correct_retry_count: int
    incorrect_retry_count: int
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    is_due: bool = False
    created_at: datetime
    updated_at: datetime

    # Question details
    question_text: str
    difficulty: str
    options: List[QuestionOptionPublic] = []
    explanation: Optional[str] = None
    hint: Optional[str] = None
    sat_shortcut: Optional[str] = None
    correct_option_id: Optional[uuid.UUID] = None
    last_selected_option_id: Optional[uuid.UUID] = None


class MistakeListResponse(BaseModel):
    items: List[MistakeEntryItem]
    total: int
    limit: int
    offset: int


class MistakeAnalyticsResponse(BaseModel):
    total_mistakes: int
    active_mistakes: int
    in_review_mistakes: int
    mastered_mistakes: int
    due_reviews: int
    mastery_rate: float
    average_retries: float
    by_subject: Dict[str, int]
    by_domain: Dict[str, int]
    by_skill: Dict[str, int]
    by_mistake_type: Dict[str, int]
