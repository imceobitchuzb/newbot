from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.question import (
    AttemptResultResponse,
    AttemptSubmitRequest,
    QuestionPublic,
)
from backend.app.services.question_service import question_service

router = APIRouter()


@router.get(
    "",
    response_model=List[QuestionPublic],
    summary="List published questions with filtering",
)
async def list_questions(
    subject: Optional[str] = Query(None, description="MATH or READING_WRITING"),
    domain: Optional[str] = Query(None, description="e.g. ALGEBRA, ADVANCED_MATH"),
    skill: Optional[str] = Query(None, description="e.g. Linear equations"),
    difficulty: Optional[str] = Query(None, description="EASY, MEDIUM, HARD"),
    limit: int = Query(20, ge=1, le=50, description="Max questions to return (max 50)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns published questions matching the filter criteria.
    Answer keys and option correctness flags are strictly withheld.
    Requires Bearer authorization.
    """
    return await question_service.list_published(
        db=db,
        subject=subject,
        domain=domain,
        skill=skill,
        difficulty=difficulty,
        limit=limit,
    )


@router.get(
    "/random",
    response_model=QuestionPublic,
    summary="Get a random published question for practice",
)
async def get_random_question(
    subject: Optional[str] = Query(None, description="MATH or READING_WRITING"),
    difficulty: Optional[str] = Query(None, description="EASY, MEDIUM, HARD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches a random published question matching optional subject/difficulty criteria.
    """
    return await question_service.get_random_for_learner(
        db=db,
        subject=subject,
        difficulty=difficulty,
    )


@router.get(
    "/{question_id}",
    response_model=QuestionPublic,
    summary="Get question by ID",
)
async def get_question_by_id(
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a single published question by UUID.
    Answer key is withheld.
    """
    return await question_service.get_for_learner(db, question_id)


@router.post(
    "/{question_id}/attempt",
    response_model=AttemptResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit an answer attempt for a question",
)
async def submit_question_attempt(
    question_id: uuid.UUID,
    payload: AttemptSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates student answer, logs the attempt with microsecond accuracy,
    and returns immediate feedback including full explanation and SAT tricks.
    """
    return await question_service.submit_attempt(
        db=db,
        user_id=current_user.id,
        question_id=question_id,
        payload=payload,
    )
