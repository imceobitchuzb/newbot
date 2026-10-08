from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class PassageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: Optional[str] = None
    passage_text: str
    source_info: Optional[str] = None


class QuestionOptionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    text: str
    order_index: int


class QuestionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject: str
    domain: str
    skill: str
    subskill: Optional[str] = None
    question_type: str
    difficulty: str
    question_text: str
    options: List[QuestionOptionPublic]
    passage: Optional[PassageResponse] = None
    estimated_time_seconds: int
    desmos_allowed: bool
    desmos_recommended: bool
    template_id: Optional[str] = None
    variant_group: Optional[str] = None
    source_type: Optional[str] = "ORIGINAL"


class AttemptSubmitRequest(BaseModel):
    selected_option_id: uuid.UUID = Field(
        ..., description="The UUID of the chosen answer option"
    )
    time_spent_seconds: int = Field(
        default=0, ge=0, le=3600, description="Time in seconds taken by the student"
    )


class AttemptResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_id: uuid.UUID
    question_id: uuid.UUID
    selected_option_id: uuid.UUID
    is_correct: bool
    correct_option_id: uuid.UUID
    explanation: str
    hint: Optional[str] = None
    sat_shortcut: Optional[str] = None
    time_spent_seconds: int
    answered_at: datetime
