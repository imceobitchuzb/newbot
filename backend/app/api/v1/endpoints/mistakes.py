from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.mistake_book import (
    MistakeAnalyticsResponse,
    MistakeClassifyRequest,
    MistakeEntryItem,
    MistakeListResponse,
    MistakeRetryRequest,
    MistakeRetryResponse,
    MistakeReviewRequest,
)
from backend.app.services.mistake_analytics_service import MistakeAnalyticsService
from backend.app.services.mistake_book_service import MistakeBookService

router = APIRouter()


@router.get(
    "",
    response_model=MistakeListResponse,
    summary="Get user mistake book entries with filtering and pagination",
)
async def list_mistakes(
    subject: Optional[str] = Query(None, description="Subject filter (MATH, READING_WRITING)"),
    domain: Optional[str] = Query(None, description="Domain filter"),
    skill: Optional[str] = Query(None, description="Skill filter"),
    status: Optional[str] = Query(None, description="Status filter (ACTIVE, IN_REVIEW, MASTERED, DISMISSED)"),
    mistake_type: Optional[str] = Query(None, description="Mistake type filter"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MistakeListResponse:
    """List mistake book entries for the authenticated user."""
    return await MistakeBookService.get_mistakes(
        db=db,
        user_id=current_user.id,
        subject=subject,
        domain=domain,
        skill=skill,
        status=status,
        mistake_type=mistake_type,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/next",
    response_model=Optional[MistakeEntryItem],
    summary="Get highest priority mistake to remediate",
)
async def get_next_priority_mistake(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[MistakeEntryItem]:
    """Retrieve the next highest-priority mistake based on review schedule and active state."""
    return await MistakeBookService.get_next_priority_mistake(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/analytics",
    response_model=MistakeAnalyticsResponse,
    summary="Get aggregated mistake analytics and review due counts",
)
async def get_mistake_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MistakeAnalyticsResponse:
    """Retrieve user's error telemetry, mastery rates, and review queue counts."""
    return await MistakeAnalyticsService.get_user_mistake_analytics(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{mistake_id}",
    response_model=MistakeEntryItem,
    summary="Get mistake entry detail",
)
async def get_mistake(
    mistake_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MistakeEntryItem:
    """Retrieve specific mistake entry with full question, explanation, and history."""
    return await MistakeBookService.get_mistake_by_id(
        db=db,
        user_id=current_user.id,
        mistake_id=mistake_id,
    )


@router.post(
    "/{mistake_id}/review",
    response_model=MistakeEntryItem,
    summary="Mark mistake as reviewed and advance spaced review schedule",
)
async def review_mistake(
    mistake_id: uuid.UUID,
    request: MistakeReviewRequest = MistakeReviewRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MistakeEntryItem:
    """Advance the review count and update next review schedule."""
    return await MistakeBookService.review_mistake(
        db=db,
        user_id=current_user.id,
        mistake_id=mistake_id,
        new_mistake_type=request.mistake_type,
    )


@router.patch(
    "/{mistake_id}/classify",
    response_model=MistakeEntryItem,
    summary="Update mistake error type classification",
)
async def classify_mistake(
    mistake_id: uuid.UUID,
    request: MistakeClassifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MistakeEntryItem:
    """Update mistake category (Concept Gap, Careless Error, Misread, etc.)."""
    return await MistakeBookService.classify_mistake(
        db=db,
        user_id=current_user.id,
        mistake_id=mistake_id,
        mistake_type=request.mistake_type,
    )


@router.post(
    "/{mistake_id}/retry",
    response_model=MistakeRetryResponse,
    summary="Retry a mistake question and evaluate mastery / regression",
)
async def retry_mistake(
    mistake_id: uuid.UUID,
    request: MistakeRetryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MistakeRetryResponse:
    """
    Submits a retry attempt for an error question:
    - Creates a new QuestionAttempt record
    - Tracks consecutive successes for Mastered status
    - Detects regression if an error occurs on a previously mastered question
    """
    return await MistakeBookService.retry_mistake(
        db=db,
        user_id=current_user.id,
        mistake_id=mistake_id,
        req=request,
    )
