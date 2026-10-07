from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.question import QuestionPublic


class DiagnosticSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    current_module: str
    current_question_index: int
    started_at: datetime
    total_questions: int = 40


class CurrentDiagnosticResponse(BaseModel):
    id: uuid.UUID
    status: str
    subject: str
    module_number: int
    current_question_index: int
    answered_in_module: int
    total_in_module: int
    total_answered: int
    total_questions: int
    progress_percent: int
    current_question: Optional[QuestionPublic] = None


class DiagnosticAnswerRequest(BaseModel):
    selected_option_id: uuid.UUID
    time_spent_seconds: int = Field(default=0, ge=0, le=3600)


class DiagnosticAnswerResponse(BaseModel):
    module_completed: bool
    diagnostic_completed: bool
    current_module: str
    current_question_index: int
    total_answered: int
    total_questions: int = 40


class DomainBreakdownItem(BaseModel):
    domain: str
    subject: str
    total_questions: int
    correct_questions: int
    accuracy: float
    classification: str


class DiagnosticResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    math_correct: int
    math_total: int
    rw_correct: int
    rw_total: int
    math_accuracy: float
    rw_accuracy: float
    total_accuracy: float
    estimated_math_low: int
    estimated_math_high: int
    estimated_rw_low: int
    estimated_rw_high: int
    estimated_total_low: int
    estimated_total_high: int
    duration_seconds: int
    domain_breakdown: List[DomainBreakdownItem]
    weak_domains: List[str]
    strong_domains: List[str]
    completed_at: datetime
