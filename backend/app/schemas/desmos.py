from datetime import datetime
from typing import Any, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DesmosOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    text: str


class DesmosTechniqueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    description: str
    technique_type: str
    subject: str
    difficulty: str
    when_to_use: str
    when_not_to_use: str
    sat_tip: str
    question_count: int = 0
    practiced_count: int = 0
    accuracy_percent: float = 0.0


class ExampleQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    domain: str
    skill: str
    difficulty: str
    question_text: str
    explanation: str
    sat_shortcut: Optional[str] = None
    options: List[DesmosOptionSchema] = Field(default_factory=list)


class DesmosTechniqueDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    description: str
    technique_type: str
    subject: str
    difficulty: str
    when_to_use: str
    when_not_to_use: str
    steps: List[str]
    common_mistakes: List[str]
    sat_tip: str
    example_question: Optional[ExampleQuestionResponse] = None
    question_count: int = 0


class DesmosTechniqueListResponse(BaseModel):
    items: List[DesmosTechniqueResponse]
    total: int


class DesmosQuestionSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject: str
    domain: str
    skill: str
    difficulty: str
    question_type: str
    question_text: str
    estimated_time_seconds: int
    desmos_allowed: bool
    desmos_recommended: bool
    status: str
    options_count: int = 0


class DesmosQuestionListResponse(BaseModel):
    items: List[DesmosQuestionSummarySchema]
    total: int



class DesmosSessionStartRequest(BaseModel):
    technique_slug: Optional[str] = None
    technique_type: Optional[str] = None
    difficulty: Optional[str] = None
    target_count: int = Field(default=10, ge=3, le=20)
    recommended_only: bool = False


class DesmosQuestionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID  # practice question id
    question_id: uuid.UUID
    order_index: int
    domain: str
    skill: str
    difficulty: str
    question_text: str
    estimated_time_seconds: int
    desmos_allowed: bool
    desmos_recommended: bool
    technique_type: Optional[str] = None
    technique_title: Optional[str] = None
    technique_slug: Optional[str] = None
    recommendation_status: str  # 'RECOMMENDED', 'ALLOWED', 'FORBIDDEN'
    recommendation_reason: str
    options: List[DesmosOptionSchema]
    is_answered: bool
    is_correct: Optional[bool] = None
    selected_option_id: Optional[uuid.UUID] = None
    time_spent_seconds: Optional[int] = None
    desmos_used: bool = True


class DesmosSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    technique_slug: Optional[str] = None
    technique_title: Optional[str] = None
    difficulty: Optional[str] = None
    target_count: int
    completed_count: int
    correct_count: int
    accuracy_percent: float
    current_question: Optional[DesmosQuestionItem] = None
    questions: List[DesmosQuestionItem]
    started_at: datetime
    completed_at: Optional[datetime] = None


class DesmosAnswerRequest(BaseModel):
    selected_option_id: uuid.UUID
    time_spent_seconds: int = Field(default=45, ge=1, le=600)
    desmos_used: bool = True


class DesmosAnswerResponse(BaseModel):
    is_correct: bool
    correct_option_id: uuid.UUID
    explanation: str
    hint: Optional[str] = None
    sat_shortcut: Optional[str] = None
    desmos_guidance: Optional[str] = None
    session_completed: bool
    session_accuracy: float
    next_question_id: Optional[uuid.UUID] = None


class TechniqueAnalyticsItem(BaseModel):
    technique_type: str
    technique_slug: str
    technique_title: str
    practiced_count: int
    correct_count: int
    accuracy_percent: float
    avg_time_seconds: float


class DesmosAnalyticsResponse(BaseModel):
    total_questions_attempted: int
    total_correct: int
    overall_accuracy: float
    avg_time_seconds: float
    recommended_count: int
    allowed_count: int
    techniques: List[TechniqueAnalyticsItem]
