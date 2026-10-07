"""Pydantic schemas for AI SAT Tutor."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.enums import (
    QuickPromptType,
    Subject,
    TutorActionType,
    TutorContextType,
    TutorMode,
)


class TutorConversationCreateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    context_type: TutorContextType = TutorContextType.GENERAL
    context_id: Optional[str] = Field(None, max_length=128)
    subject: Optional[Subject] = None


class TutorMessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    mode: TutorMode = TutorMode.HINT
    quick_prompt: Optional[QuickPromptType] = None


class TutorActionSchema(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    target_id: Optional[str] = None
    url: Optional[str] = None


class TutorMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    mode: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class TutorConversationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: Optional[str] = None
    context_type: str
    context_id: Optional[str] = None
    subject: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_preview: Optional[str] = None


class TutorConversationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: Optional[str] = None
    context_type: str
    context_id: Optional[str] = None
    subject: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[TutorMessageResponse] = []


class TutorExplainRequest(BaseModel):
    question_id: Optional[UUID] = None
    mistake_id: Optional[UUID] = None
    mode: TutorMode = TutorMode.HINT
    prompt: Optional[str] = Field(None, max_length=4000)


class TutorExplainResponse(BaseModel):
    message: str
    mode: str
    actions: List[Dict[str, Any]] = []
    suggested_skill: Optional[str] = None
    suggested_technique: Optional[str] = None
