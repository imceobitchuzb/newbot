from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.math_practice import (
    DomainAnalyticsOut,
    MathAnalyticsResponse,
    MathPracticeAnswerRequest,
    MathPracticeAnswerResponse,
    MathPracticeResultResponse,
    MathPracticeSessionResponse,
    MathPracticeStartRequest,
)
from backend.app.services.math_analytics_service import MathAnalyticsService
from backend.app.services.math_practice_service import MathPracticeService

router = APIRouter()


@router.post(
    "/practice",
    response_model=MathPracticeSessionResponse,
    summary="Start or resume a math practice session",
)
async def start_practice_session(
    request: MathPracticeStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MathPracticeSessionResponse:
    """Start a new customized Math practice session or resume an active one."""
    return await MathPracticeService.start_practice_session(
        db=db,
        user_id=current_user.id,
        req=request,
    )


@router.get(
    "/practice/current",
    response_model=Optional[MathPracticeSessionResponse],
    summary="Get user's currently active practice session",
)
async def get_current_practice_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[MathPracticeSessionResponse]:
    """Retrieve the currently active IN_PROGRESS practice session for the user."""
    return await MathPracticeService.get_current_session(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/practice/{session_id}",
    response_model=MathPracticeSessionResponse,
    summary="Get practice session by ID",
)
async def get_practice_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MathPracticeSessionResponse:
    """Retrieve a practice session and its questions."""
    return await MathPracticeService.get_session_by_id(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
    )


@router.post(
    "/practice/{session_id}/questions/{practice_question_id}/answer",
    response_model=MathPracticeAnswerResponse,
    summary="Submit answer for a practice question",
)
async def submit_practice_answer(
    session_id: uuid.UUID,
    practice_question_id: uuid.UUID,
    request: MathPracticeAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MathPracticeAnswerResponse:
    """
    Submits an answer to a question within a practice session.
    Provides immediate feedback with explanation, hint, SAT shortcut, and correct answer.
    """
    return await MathPracticeService.submit_answer(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        practice_question_id=practice_question_id,
        req=request,
    )


@router.get(
    "/practice/{session_id}/result",
    response_model=MathPracticeResultResponse,
    summary="Get practice session completion results",
)
async def get_practice_result(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MathPracticeResultResponse:
    """Retrieve summary results, domain breakdown, and question review for a practice session."""
    return await MathPracticeService.get_session_result(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
    )


@router.get(
    "/analytics",
    response_model=MathAnalyticsResponse,
    summary="Get math analytics and mastery overview",
)
async def get_math_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MathAnalyticsResponse:
    """Retrieve user's real math mastery breakdown across all 4 domains and canonical skills."""
    return await MathAnalyticsService.get_user_math_analytics(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/domains/{domain}",
    response_model=DomainAnalyticsOut,
    summary="Get single math domain analytics",
)
async def get_domain_analytics(
    domain: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DomainAnalyticsOut:
    """Retrieve detailed skill-by-skill analytics for a specific Math domain."""
    res = await MathAnalyticsService.get_domain_analytics(
        db=db,
        user_id=current_user.id,
        domain_name=domain,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain '{domain}' not found in SAT Math taxonomy.",
        )
    return res
