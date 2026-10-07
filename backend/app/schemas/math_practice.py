from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.question import QuestionOptionPublic



class MathPracticeStartRequest(BaseModel):
    domain: Optional[str] = None
    difficulty: Optional[str] = None
    skill: Optional[str] = None
    question_count: int = Field(default=10, ge=3, le=25)


class MathPracticeQuestionItem(BaseModel):
    practice_question_id: uuid.UUID
    question_id: uuid.UUID
    order_index: int
    is_answered: bool
    selected_option_id: Optional[uuid.UUID] = None
    is_correct: Optional[bool] = None
    time_spent_seconds: int = 0
    domain: str
    skill: str
    difficulty: str
    question_text: str
    options: List[QuestionOptionPublic]
    desmos_allowed: bool = True
    desmos_recommended: bool = False
    # Only populated after answered
    explanation: Optional[str] = None
    hint: Optional[str] = None
    sat_shortcut: Optional[str] = None
    correct_option_id: Optional[uuid.UUID] = None


class MathPracticeSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    domain: Optional[str] = None
    difficulty: Optional[str] = None
    skill: Optional[str] = None
    total_questions: int
    current_question_index: int
    answered_count: int
    correct_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_question: Optional[MathPracticeQuestionItem] = None
    questions: List[MathPracticeQuestionItem] = []


class MathPracticeAnswerRequest(BaseModel):
    selected_option_id: uuid.UUID
    time_spent_seconds: int = Field(default=0, ge=0, le=3600)


class MathPracticeAnswerResponse(BaseModel):
    is_correct: bool
    selected_option_id: uuid.UUID
    correct_option_id: uuid.UUID
    explanation: str
    hint: Optional[str] = None
    sat_shortcut: Optional[str] = None
    session_completed: bool
    next_question_index: int


class MathPracticeResultResponse(BaseModel):
    session_id: uuid.UUID
    domain: Optional[str] = None
    difficulty: Optional[str] = None
    skill: Optional[str] = None
    total_questions: int
    answered_questions: int
    correct_count: int
    accuracy_percentage: float
    total_time_seconds: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    domain_breakdown: Dict[str, Dict[str, Any]]
    questions: List[MathPracticeQuestionItem]


class SkillAnalyticsOut(BaseModel):
    skill: str
    attempts: int
    correct: int
    accuracy: float
    mastery_level: str


class DomainAnalyticsOut(BaseModel):
    domain: str
    title: str
    description: str
    total_attempts: int
    correct_attempts: int
    accuracy: float
    mastery_level: str
    skills: List[SkillAnalyticsOut]


class MathAnalyticsResponse(BaseModel):
    total_attempts: int
    correct_attempts: int
    overall_accuracy: float
    estimated_score_range: Optional[str] = None
    domains: List[DomainAnalyticsOut]
    recommended_focus_skill: Optional[str] = None
    recommended_focus_domain: Optional[str] = None
