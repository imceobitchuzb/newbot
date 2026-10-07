from datetime import datetime, timezone
from typing import Optional, Set
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.adaptive import (
    AdaptivePracticeQuestion,
    AdaptivePracticeSession,
    AdaptiveProfile,
)
from backend.app.models.enums import (
    AdaptiveSessionStatus,
    Difficulty,
    RecommendationType,
    Subject,
)
from backend.app.models.question import Question, QuestionAttempt, QuestionOption
from backend.app.schemas.adaptive import (
    AdaptiveAnswerResponse,
    AdaptiveQuestionItem,
    AdaptiveSessionResponse,
    AdaptiveSessionSummary,
)
from backend.app.schemas.question import QuestionPublic
from backend.app.services.adaptive_engine_service import AdaptiveEngineService
from backend.app.services.mistake_book_service import MistakeBookService


class AdaptiveSessionService:
    """Manages adaptive practice sessions and atomic answer processing."""

    @classmethod
    async def get_or_create_profile(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        subject: str = Subject.MATH.value,
    ) -> AdaptiveProfile:
        stmt = (
            select(AdaptiveProfile)
            .where(
                AdaptiveProfile.user_id == user_id,
                AdaptiveProfile.subject == subject,
            )
        )
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile:
            profile = AdaptiveProfile(
                user_id=user_id,
                subject=subject,
                current_difficulty=Difficulty.MEDIUM.value,
                total_questions=0,
                total_correct=0,
                last_active_at=datetime.now(timezone.utc),
            )
            db.add(profile)
            await db.flush()
        return profile

    @classmethod
    async def start_or_resume_session(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        subject: str = Subject.MATH.value,
        total_questions: int = 10,
    ) -> AdaptiveSessionResponse:
        """
        Idempotently starts a new adaptive session or returns an active in-progress session.
        """
        # 1. Check for active session
        active_stmt = (
            select(AdaptivePracticeSession)
            .where(
                AdaptivePracticeSession.user_id == user_id,
                AdaptivePracticeSession.subject == subject,
                AdaptivePracticeSession.status == AdaptiveSessionStatus.IN_PROGRESS.value,
            )
            .options(
                selectinload(AdaptivePracticeSession.questions)
                .selectinload(AdaptivePracticeQuestion.question)
                .selectinload(Question.options),
                selectinload(AdaptivePracticeSession.questions)
                .selectinload(AdaptivePracticeQuestion.question)
                .selectinload(Question.passage),
            )
            .order_by(AdaptivePracticeSession.created_at.desc())
        )
        res = await db.execute(active_stmt)
        active_sess = res.scalars().first()

        if active_sess:
            return cls._build_session_response(active_sess)

        # 2. Start a fresh session
        profile = await cls.get_or_create_profile(db, user_id, subject)
        init_diff = profile.current_difficulty

        # Get initial recommendation
        rec_type, domain, skill, diff, reason, mistake_qid = (
            await AdaptiveEngineService.determine_next_recommendation(
                db=db,
                user_id=user_id,
                subject=subject,
                current_difficulty=init_diff,
            )
        )

        first_q = await AdaptiveEngineService.select_question(
            db=db,
            user_id=user_id,
            target_domain=domain,
            target_skill=skill,
            target_difficulty=diff,
            excluded_question_ids=set(),
            subject=subject,
            force_question_id=mistake_qid,
        )

        if not first_q:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to select question from pool. Question bank may be empty.",
            )

        now = datetime.now(timezone.utc)
        sess = AdaptivePracticeSession(
            user_id=user_id,
            subject=subject,
            current_question_index=0,
            total_questions=total_questions,
            current_difficulty=diff,
            status=AdaptiveSessionStatus.IN_PROGRESS.value,
            started_at=now,
        )
        db.add(sess)
        await db.flush()

        apq = AdaptivePracticeQuestion(
            session_id=sess.id,
            question_id=first_q.id,
            order_index=0,
            difficulty_at_assignment=first_q.difficulty,
            recommendation_type=rec_type,
            reason=reason,
            is_answered=False,
        )
        db.add(apq)
        await db.commit()

        # Reload with options/passage
        return await cls.get_session_by_id(db, user_id, sess.id)

    @classmethod
    async def get_session_by_id(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> AdaptiveSessionResponse:
        stmt = (
            select(AdaptivePracticeSession)
            .where(
                AdaptivePracticeSession.id == session_id,
                AdaptivePracticeSession.user_id == user_id,
            )
            .options(
                selectinload(AdaptivePracticeSession.questions)
                .selectinload(AdaptivePracticeQuestion.question)
                .selectinload(Question.options),
                selectinload(AdaptivePracticeSession.questions)
                .selectinload(AdaptivePracticeQuestion.question)
                .selectinload(Question.passage),
            )
        )
        res = await db.execute(stmt)
        sess = res.scalar_one_or_none()
        if not sess:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adaptive session not found.",
            )
        return cls._build_session_response(sess)

    @classmethod
    async def get_current_session(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        subject: str = Subject.MATH.value,
    ) -> Optional[AdaptiveSessionResponse]:
        stmt = (
            select(AdaptivePracticeSession)
            .where(
                AdaptivePracticeSession.user_id == user_id,
                AdaptivePracticeSession.subject == subject,
                AdaptivePracticeSession.status == AdaptiveSessionStatus.IN_PROGRESS.value,
            )
            .options(
                selectinload(AdaptivePracticeSession.questions)
                .selectinload(AdaptivePracticeQuestion.question)
                .selectinload(Question.options),
                selectinload(AdaptivePracticeSession.questions)
                .selectinload(AdaptivePracticeQuestion.question)
                .selectinload(Question.passage),
            )
            .order_by(AdaptivePracticeSession.created_at.desc())
        )
        res = await db.execute(stmt)
        sess = res.scalars().first()
        if not sess:
            return None
        return cls._build_session_response(sess)

    @classmethod
    async def submit_answer(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        selected_option_id: uuid.UUID,
        time_spent_seconds: int = 0,
    ) -> AdaptiveAnswerResponse:
        """
        Submits answer in a single atomic transaction:
        1. Validate inputs and question assignment
        2. Create QuestionAttempt
        3. Update Mistake Book
        4. Mark AdaptivePracticeQuestion as answered
        5. Adjust adaptive difficulty
        6. Select and assign next question (or complete session)
        7. Update AdaptiveProfile
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch session
        stmt = (
            select(AdaptivePracticeSession)
            .where(
                AdaptivePracticeSession.id == session_id,
                AdaptivePracticeSession.user_id == user_id,
            )
            .options(
                selectinload(AdaptivePracticeSession.questions)
                .selectinload(AdaptivePracticeQuestion.question)
                .selectinload(Question.options),
                selectinload(AdaptivePracticeSession.questions)
                .selectinload(AdaptivePracticeQuestion.question)
                .selectinload(Question.passage),
            )
        )
        res = await db.execute(stmt)
        sess = res.scalar_one_or_none()

        if not sess:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adaptive practice session not found.",
            )

        if sess.status != AdaptiveSessionStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is already {sess.status.lower()}.",
            )

        # 2. Find target question assignment in session
        target_apq = next(
            (q for q in sess.questions if q.question_id == question_id),
            None,
        )
        if not target_apq:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question does not belong to this adaptive session.",
            )

        if target_apq.is_answered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This adaptive question has already been answered.",
            )

        # 3. Validate option belongs to question
        q_obj = target_apq.question
        chosen_opt = next((o for o in q_obj.options if o.id == selected_option_id), None)
        if not chosen_opt:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected option does not belong to the question.",
            )

        correct_opt = next((o for o in q_obj.options if o.is_correct), q_obj.options[0])
        is_correct = bool(chosen_opt.is_correct)

        # 4. Create QuestionAttempt
        attempt = QuestionAttempt(
            user_id=user_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            is_correct=is_correct,
            time_spent_seconds=time_spent_seconds,
            answered_at=now,
        )
        db.add(attempt)
        await db.flush()

        # 5. Mistake Book synchronization
        if not is_correct:
            await MistakeBookService.record_or_update_mistake(
                db=db,
                user_id=user_id,
                question_id=question_id,
                attempt_id=attempt.id,
                subject=q_obj.subject,
                domain=q_obj.domain,
                skill=q_obj.skill,
                time_spent_seconds=time_spent_seconds,
                estimated_time_seconds=q_obj.estimated_time_seconds,
            )

        # 6. Mark target question as answered
        target_apq.is_answered = True
        target_apq.selected_option_id = selected_option_id
        target_apq.is_correct = is_correct
        target_apq.time_spent_seconds = time_spent_seconds
        target_apq.answered_at = now

        # 7. Calculate next difficulty
        # Collect recent outcomes from this session
        session_outcomes = [
            q.is_correct for q in sess.questions if q.is_answered and q.is_correct is not None
        ]
        # Invert to newest first
        session_outcomes.reverse()
        next_diff = AdaptiveEngineService.calculate_next_difficulty(
            sess.current_difficulty,
            session_outcomes,
        )
        sess.current_difficulty = next_diff

        # 8. Check for session completion
        is_completed = (sess.current_question_index + 1) >= sess.total_questions
        next_apq_item: Optional[AdaptiveQuestionItem] = None
        session_summary: Optional[AdaptiveSessionSummary] = None

        if is_completed:
            sess.status = AdaptiveSessionStatus.COMPLETED.value
            sess.completed_at = now

            # Build summary
            answered_questions = [q for q in sess.questions if q.is_answered]
            total_corr = sum(1 for q in answered_questions if q.is_correct)
            skills_practiced = list(dict.fromkeys(q.question.skill for q in answered_questions))
            diff_progression = [q.difficulty_at_assignment for q in answered_questions]

            # Recommendation for future practice
            _, next_domain, next_skill, _, _, _ = (
                await AdaptiveEngineService.determine_next_recommendation(
                    db=db,
                    user_id=user_id,
                    subject=sess.subject,
                    current_difficulty=next_diff,
                )
            )

            session_summary = AdaptiveSessionSummary(
                total_completed=len(answered_questions),
                total_correct=total_corr,
                accuracy=round(total_corr / float(len(answered_questions)), 4) if answered_questions else 0.0,
                skills_practiced=skills_practiced,
                difficulty_progression=diff_progression,
                next_recommended_skill=next_skill,
                next_recommended_difficulty=next_diff,
            )
        else:
            # Progress index
            sess.current_question_index += 1

            # Determine next question
            assigned_qids = {q.question_id for q in sess.questions}
            rec_type, domain, skill, diff, reason, mistake_qid = (
                await AdaptiveEngineService.determine_next_recommendation(
                    db=db,
                    user_id=user_id,
                    subject=sess.subject,
                    current_difficulty=next_diff,
                )
            )

            next_q = await AdaptiveEngineService.select_question(
                db=db,
                user_id=user_id,
                target_domain=domain,
                target_skill=skill,
                target_difficulty=diff,
                excluded_question_ids=assigned_qids,
                subject=sess.subject,
                force_question_id=mistake_qid,
            )

            if next_q:
                new_apq = AdaptivePracticeQuestion(
                    session_id=sess.id,
                    question_id=next_q.id,
                    order_index=sess.current_question_index,
                    difficulty_at_assignment=next_q.difficulty,
                    recommendation_type=rec_type,
                    reason=reason,
                    is_answered=False,
                )
                db.add(new_apq)
                await db.flush()

                next_apq_item = AdaptiveQuestionItem(
                    id=new_apq.id,
                    session_id=new_apq.session_id,
                    question_id=new_apq.question_id,
                    order_index=new_apq.order_index,
                    difficulty_at_assignment=new_apq.difficulty_at_assignment,
                    recommendation_type=new_apq.recommendation_type,
                    reason=new_apq.reason,
                    is_answered=False,
                    question=QuestionPublic.model_validate(next_q),
                )

        # 9. Update AdaptiveProfile
        profile = await cls.get_or_create_profile(db, user_id, sess.subject)
        profile.total_questions += 1
        if is_correct:
            profile.total_correct += 1
        profile.current_difficulty = next_diff
        profile.last_active_at = now

        await db.commit()

        return AdaptiveAnswerResponse(
            is_correct=is_correct,
            selected_option_id=chosen_opt.id,
            correct_option_id=correct_opt.id,
            explanation=q_obj.explanation,
            hint=q_obj.hint,
            sat_shortcut=q_obj.sat_shortcut,
            session_completed=is_completed,
            next_difficulty=next_diff,
            next_question=next_apq_item,
            session_summary=session_summary,
        )

    @classmethod
    def _build_session_response(
        cls,
        sess: AdaptivePracticeSession,
    ) -> AdaptiveSessionResponse:
        current_apq = next(
            (q for q in sess.questions if not q.is_answered),
            None,
        )
        if not current_apq and sess.questions:
            # If all are answered or on last, take the last
            current_apq = sess.questions[-1]

        apq_item = None
        if current_apq and current_apq.question:
            apq_item = AdaptiveQuestionItem(
                id=current_apq.id,
                session_id=current_apq.session_id,
                question_id=current_apq.question_id,
                order_index=current_apq.order_index,
                difficulty_at_assignment=current_apq.difficulty_at_assignment,
                recommendation_type=current_apq.recommendation_type,
                reason=current_apq.reason,
                is_answered=current_apq.is_answered,
                question=QuestionPublic.model_validate(current_apq.question),
            )

        return AdaptiveSessionResponse(
            id=sess.id,
            user_id=sess.user_id,
            subject=sess.subject,
            current_question_index=sess.current_question_index,
            total_questions=sess.total_questions,
            current_difficulty=sess.current_difficulty,
            status=sess.status,
            current_question=apq_item,
            started_at=sess.started_at,
            completed_at=sess.completed_at,
        )
