from datetime import datetime
from typing import Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.question import QuestionPublic


class SkillMasteryItem(BaseModel):
    skill: str
    domain: str
    status: str
    mastery_score: float
    confidence_score: float
    attempts: int
    accuracy: float
    recent_accuracy: float
    easy_accuracy: float
    medium_accuracy: float
    hard_accuracy: float
    has_active_mistake: bool = False


class AdaptiveAnalyticsResponse(BaseModel):
    overall_mastery: float
    mastered_skills_count: int
    learning_skills_count: int
    practicing_skills_count: int
    strong_skills_count: int
    recommended_skill: str
    recommended_domain: str
    current_difficulty: str
    confidence: float
    recent_accuracy: float
    skills: List[SkillMasteryItem]


class AdaptiveNextQuestionResponse(BaseModel):
    question: QuestionPublic
    recommendation_type: str
    domain: str
    skill: str
    difficulty: str
    reason: str


class AdaptiveSessionStartRequest(BaseModel):
    total_questions: int = Field(default=10, ge=3, le=25)
    subject: str = Field(default="MATH")


class AdaptiveQuestionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    question_id: uuid.UUID
    order_index: int
    difficulty_at_assignment: str
    recommendation_type: str
    reason: Optional[str] = None
    is_answered: bool
    question: QuestionPublic


class AdaptiveSessionSummary(BaseModel):
    total_completed: int
    total_correct: int
    accuracy: float
    skills_practiced: List[str]
    difficulty_progression: List[str]
    next_recommended_skill: str
    next_recommended_difficulty: str


class AdaptiveSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    subject: str
    current_question_index: int
    total_questions: int
    current_difficulty: str
    status: str
    current_question: Optional[AdaptiveQuestionItem] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class AdaptiveAnswerRequest(BaseModel):
    selected_option_id: uuid.UUID
    time_spent_seconds: int = Field(default=0, ge=0, le=3600)


class AdaptiveAnswerResponse(BaseModel):
    is_correct: bool
    selected_option_id: uuid.UUID
    correct_option_id: uuid.UUID
    explanation: str
    hint: Optional[str] = None
    sat_shortcut: Optional[str] = None
    session_completed: bool
    next_difficulty: str
    next_question: Optional[AdaptiveQuestionItem] = None
    session_summary: Optional[AdaptiveSessionSummary] = None
