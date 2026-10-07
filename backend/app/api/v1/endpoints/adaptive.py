from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.enums import AdaptiveSkillStatus, Difficulty, Subject
from backend.app.models.user import User
from backend.app.schemas.adaptive import (
    AdaptiveAnalyticsResponse,
    AdaptiveAnswerRequest,
    AdaptiveAnswerResponse,
    AdaptiveNextQuestionResponse,
    AdaptiveSessionResponse,
    AdaptiveSessionStartRequest,
)
from backend.app.schemas.question import QuestionPublic
from backend.app.services.adaptive_engine_service import AdaptiveEngineService
from backend.app.services.adaptive_session_service import AdaptiveSessionService

router = APIRouter(prefix="/adaptive", tags=["Adaptive Learning Engine"])


@router.get("/next", response_model=AdaptiveNextQuestionResponse)
async def get_next_adaptive_question(
    subject: str = Query(default=Subject.MATH.value),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns standalone deterministic next question recommendation without leaking answer key.
    """
    profile = await AdaptiveSessionService.get_or_create_profile(db, current_user.id, subject)
    rec_type, domain, skill, diff, reason, mistake_qid = (
        await AdaptiveEngineService.determine_next_recommendation(
            db=db,
            user_id=current_user.id,
            subject=subject,
            current_difficulty=profile.current_difficulty,
        )
    )

    q = await AdaptiveEngineService.select_question(
        db=db,
        user_id=current_user.id,
        target_domain=domain,
        target_skill=skill,
        target_difficulty=diff,
        subject=subject,
        force_question_id=mistake_qid,
    )

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions available for recommendation in question bank.",
        )

    return AdaptiveNextQuestionResponse(
        question=QuestionPublic.model_validate(q),
        recommendation_type=rec_type,
        domain=domain,
        skill=skill,
        difficulty=q.difficulty,
        reason=reason,
    )


@router.get("/analytics", response_model=AdaptiveAnalyticsResponse)
async def get_adaptive_analytics(
    subject: str = Query(default=Subject.MATH.value),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns complete deterministic mastery telemetry, skill states, and curriculum trajectory.
    """
    profile = await AdaptiveSessionService.get_or_create_profile(db, current_user.id, subject)
    skills_map = await AdaptiveEngineService.get_user_skill_analytics(db, current_user.id, subject)
    skills_list = list(skills_map.values())

    # Overall mastery = average of mastery across all canonical skills
    overall_mastery = (
        round(sum(s.mastery_score for s in skills_list) / float(len(skills_list)), 4)
        if skills_list
        else 0.0
    )

    mastered_count = sum(1 for s in skills_list if s.status == AdaptiveSkillStatus.MASTERED.value)
    strong_count = sum(1 for s in skills_list if s.status == AdaptiveSkillStatus.STRONG.value)
    practicing_count = sum(1 for s in skills_list if s.status == AdaptiveSkillStatus.PRACTICING.value)
    learning_count = sum(1 for s in skills_list if s.status == AdaptiveSkillStatus.LEARNING.value)

    # Next recommendation
    _, rec_domain, rec_skill, _, _, _ = (
        await AdaptiveEngineService.determine_next_recommendation(
            db=db,
            user_id=current_user.id,
            subject=subject,
            current_difficulty=profile.current_difficulty,
        )
    )

    # Overall confidence and recent accuracy
    total_att = sum(s.attempts for s in skills_list)
    overall_conf = AdaptiveEngineService.calculate_confidence(total_att)
    attempted_skills = [s for s in skills_list if s.attempts > 0]
    avg_recent_acc = (
        round(sum(s.recent_accuracy for s in attempted_skills) / float(len(attempted_skills)), 4)
        if attempted_skills
        else 0.0
    )

    return AdaptiveAnalyticsResponse(
        overall_mastery=overall_mastery,
        mastered_skills_count=mastered_count,
        learning_skills_count=learning_count,
        practicing_skills_count=practicing_count,
        strong_skills_count=strong_count,
        recommended_skill=rec_skill,
        recommended_domain=rec_domain,
        current_difficulty=profile.current_difficulty,
        confidence=overall_conf,
        recent_accuracy=avg_recent_acc,
        skills=skills_list,
    )


@router.post("/session", response_model=AdaptiveSessionResponse)
async def start_or_resume_session(
    payload: AdaptiveSessionStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Starts a new adaptive practice session or resumes an in-progress session.
    """
    return await AdaptiveSessionService.start_or_resume_session(
        db=db,
        user_id=current_user.id,
        subject=payload.subject,
        total_questions=payload.total_questions,
    )


@router.get("/session/current", response_model=Optional[AdaptiveSessionResponse])
async def get_current_session(
    subject: str = Query(default=Subject.MATH.value),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves currently active in-progress adaptive session if any.
    """
    return await AdaptiveSessionService.get_current_session(
        db=db,
        user_id=current_user.id,
        subject=subject,
    )


@router.get("/session/{session_id}", response_model=AdaptiveSessionResponse)
async def get_session_by_id(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves specific adaptive practice session by ID.
    """
    return await AdaptiveSessionService.get_session_by_id(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
    )


@router.post("/session/{session_id}/questions/{question_id}/answer", response_model=AdaptiveAnswerResponse)
@router.post("/{session_id}/questions/{question_id}/answer", response_model=AdaptiveAnswerResponse)
async def submit_adaptive_answer(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: AdaptiveAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits answer, evaluates outcome, adjusts difficulty, updates Mistake Book,
    and assigns next question or completes session in a single atomic transaction.
    """
    return await AdaptiveSessionService.submit_answer(
        db=db,
        user_id=current_user.id,
        session_id=session_id,
        question_id=question_id,
        selected_option_id=payload.selected_option_id,
        time_spent_seconds=payload.time_spent_seconds,
    )
