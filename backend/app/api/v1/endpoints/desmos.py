from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.desmos import QuestionDesmosTechnique
from backend.app.models.question import Question
from backend.app.models.user import User
from backend.app.schemas.desmos import (
    DesmosAnalyticsResponse,
    DesmosAnswerRequest,
    DesmosAnswerResponse,
    DesmosQuestionItem,
    DesmosQuestionListResponse,
    DesmosQuestionSummarySchema,
    DesmosSessionResponse,
    DesmosSessionStartRequest,
    DesmosTechniqueDetailResponse,
    DesmosTechniqueListResponse,
)
from backend.app.services.desmos_service import DesmosService

router = APIRouter(prefix="/desmos", tags=["desmos"])


@router.get("/techniques", response_model=DesmosTechniqueListResponse)
async def list_techniques(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DesmosTechniqueListResponse:
    """List all canonical SAT Desmos techniques with user practice stats."""
    return await DesmosService.list_techniques(db=db, user_id=current_user.id)


@router.get("/techniques/{slug}", response_model=DesmosTechniqueDetailResponse)
async def get_technique_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DesmosTechniqueDetailResponse:
    """Get full details of a specific Desmos technique by slug."""
    return await DesmosService.get_technique_by_slug(db=db, slug=slug)


@router.get("/questions", response_model=DesmosQuestionListResponse)
async def get_desmos_questions(
    technique_slug: Optional[str] = Query(None, description="Filter by technique slug"),
    recommended_only: bool = Query(False, description="Filter by desmos_recommended == True"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DesmosQuestionListResponse:
    """Query Math questions where Desmos is permitted, optionally filtered by technique."""
    query = (
        select(Question)
        .where(
            Question.subject == "MATH",
            Question.desmos_allowed == True,
        )
        .options(selectinload(Question.options))
    )

    if recommended_only:
        query = query.where(Question.desmos_recommended == True)
    if difficulty:
        query = query.where(Question.difficulty == difficulty.upper())

    if technique_slug:
        # Join with QuestionDesmosTechnique
        tech_detail = await DesmosService.get_technique_by_slug(db=db, slug=technique_slug)
        query = query.join(
            QuestionDesmosTechnique,
            Question.id == QuestionDesmosTechnique.question_id,
        ).where(QuestionDesmosTechnique.technique_id == tech_detail.id)

    query = query.order_by(Question.id.asc()).offset(offset).limit(limit)
    res = await db.execute(query)
    questions = res.scalars().all()

    items = [
        DesmosQuestionSummarySchema(
            id=q.id,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
            difficulty=q.difficulty,
            question_type=q.question_type,
            question_text=q.question_text[:120],
            estimated_time_seconds=q.estimated_time_seconds,
            desmos_allowed=q.desmos_allowed,
            desmos_recommended=q.desmos_recommended,
            status=q.status,
            options_count=len(q.options),
        )
        for q in questions
    ]

    return DesmosQuestionListResponse(items=items, total=len(items))



@router.post("/session", response_model=DesmosSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_practice_session(
    req: DesmosSessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DesmosSessionResponse:
    """Start or resume a Desmos practice session."""
    return await DesmosService.start_or_resume_session(
        db=db,
        user_id=current_user.id,
        req=req,
    )


@router.get("/session/current", response_model=Optional[DesmosSessionResponse])
async def get_current_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[DesmosSessionResponse]:
    """Retrieve active Desmos practice session if one exists."""
    return await DesmosService.get_current_session(db=db, user_id=current_user.id)


@router.get("/session/{session_id}", response_model=DesmosSessionResponse)
async def get_session_by_id(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DesmosSessionResponse:
    """Retrieve specific Desmos practice session by ID."""
    return await DesmosService.get_session_by_id(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
    )


@router.post("/session/{session_id}/questions/{question_id}/answer", response_model=DesmosAnswerResponse)
async def submit_answer(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    req: DesmosAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DesmosAnswerResponse:
    """Submit an answer to a question in a Desmos practice session."""
    return await DesmosService.submit_answer(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        question_id=question_id,
        req=req,
    )


@router.post("/session/{session_id}/abandon", response_model=DesmosSessionResponse)
async def abandon_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DesmosSessionResponse:
    """Abandon an in-progress Desmos practice session."""
    return await DesmosService.abandon_session(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
    )


@router.get("/analytics", response_model=DesmosAnalyticsResponse)
async def get_desmos_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DesmosAnalyticsResponse:
    """Retrieve user's Desmos usage analytics and technique mastery."""
    return await DesmosService.get_user_desmos_analytics(
        db=db,
        user_id=current_user.id,
    )
