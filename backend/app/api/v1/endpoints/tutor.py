"""API endpoints for AI SAT Tutor."""
from typing import Any, Dict, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.enums import TutorMode
from backend.app.models.user import User
from backend.app.schemas.tutor import (
    TutorConversationCreateRequest,
    TutorConversationDetailResponse,
    TutorConversationSummaryResponse,
    TutorExplainRequest,
    TutorExplainResponse,
    TutorMessageResponse,
    TutorMessageSendRequest,
)
from backend.app.services.tutor_context_builder import TutorContextBuilder
from backend.app.services.tutor_service import TutorService

router = APIRouter()


@router.post(
    "/conversations",
    response_model=TutorConversationDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new persistent tutor conversation",
)
async def create_conversation(
    req: TutorConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await TutorService.create_conversation(db, current_user.id, req)
    return await TutorService.get_conversation(db, current_user.id, conv.id)


@router.get(
    "/conversations",
    response_model=List[TutorConversationSummaryResponse],
    summary="List all tutor conversations for the current user",
)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TutorService.list_conversations(db, current_user.id)


@router.get(
    "/conversations/{conversation_id}",
    response_model=TutorConversationDetailResponse,
    summary="Get conversation detail with message history",
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TutorService.get_conversation(db, current_user.id, conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tutor conversation",
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await TutorService.delete_conversation(db, current_user.id, conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=TutorMessageResponse,
    summary="Send a message to the AI Tutor and receive a structured response",
)
async def send_message(
    conversation_id: UUID,
    req: TutorMessageSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TutorService.send_message(db, current_user.id, conversation_id, req)


@router.post(
    "/explain",
    response_model=TutorExplainResponse,
    summary="One-shot explanation or hint for question/mistake",
)
async def explain_one_shot(
    req: TutorExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TutorService.explain_one_shot(db, current_user.id, req)


@router.get(
    "/context/question/{question_id}",
    response_model=Dict[str, Any],
    summary="Preview question context with anti-leakage protection",
)
async def get_question_context(
    question_id: UUID,
    mode: TutorMode = TutorMode.HINT,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctx = await TutorContextBuilder.build_question_context(db, question_id, mode)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found.",
        )
    return ctx


@router.get(
    "/context/mistake/{mistake_id}",
    response_model=Dict[str, Any],
    summary="Preview mistake context for remediation",
)
async def get_mistake_context(
    mistake_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctx = await TutorContextBuilder.build_mistake_context(db, mistake_id, current_user.id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mistake entry not found or access denied.",
        )
    return ctx


@router.get(
    "/context/skill/{skill}",
    response_model=Dict[str, Any],
    summary="Preview skill context and user mastery",
)
async def get_skill_context(
    skill: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    summary = await TutorContextBuilder.get_user_summary_context(db, current_user.id)
    return {
        "skill": skill,
        "target_score": summary.get("target_score", 1400),
        "current_estimate": summary.get("current_score_estimate", 700),
    }
