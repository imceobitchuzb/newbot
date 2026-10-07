from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.core.logging import logger
from backend.app.core.math_taxonomy import normalize_skill
from backend.app.models.enums import (
    Difficulty,
    MathDomain,
    MathPracticeSessionStatus,
    QuestionStatus,
    Subject,
)
from backend.app.models.math_practice import MathPracticeQuestion, MathPracticeSession
from backend.app.models.question import Question, QuestionAttempt, QuestionOption
from backend.app.schemas.math_practice import (
    MathPracticeAnswerRequest,
    MathPracticeAnswerResponse,
    MathPracticeQuestionItem,
    MathPracticeResultResponse,
    MathPracticeSessionResponse,
    MathPracticeStartRequest,
)
from backend.app.schemas.question import QuestionOptionPublic
from backend.app.services.mistake_book_service import MistakeBookService


class MathPracticeService:
    @staticmethod
    def _format_question_item(
        pq: MathPracticeQuestion,
        q: Question,
    ) -> MathPracticeQuestionItem:
        """Format a practice question with answer security protections."""
        options_public = [
            QuestionOptionPublic(
                id=opt.id,
                label=opt.label,
                text=opt.text,
                order_index=opt.order_index,
            )
            for opt in sorted(q.options, key=lambda o: o.order_index)
        ]

        item = MathPracticeQuestionItem(
            practice_question_id=pq.id,
            question_id=q.id,
            order_index=pq.order_index,
            is_answered=pq.is_answered,
            selected_option_id=pq.selected_option_id,
            is_correct=pq.is_correct,
            time_spent_seconds=pq.time_spent_seconds,
            domain=q.domain,
            skill=q.skill,
            difficulty=q.difficulty,
            question_text=q.question_text,
            options=options_public,
            desmos_allowed=q.desmos_allowed,
            desmos_recommended=q.desmos_recommended,
        )

        # Reveal explanations and correct answer ONLY if answered
        if pq.is_answered:
            item.explanation = q.explanation
            item.hint = q.hint
            item.sat_shortcut = q.sat_shortcut
            correct_opt = next((o for o in q.options if o.is_correct), None)
            if correct_opt:
                item.correct_option_id = correct_opt.id

        return item

    @staticmethod
    def _format_session_response(
        session: MathPracticeSession,
    ) -> MathPracticeSessionResponse:
        """Construct public session representation."""
        sorted_pqs = sorted(session.questions, key=lambda p: p.order_index)
        question_items: List[MathPracticeQuestionItem] = [
            MathPracticeService._format_question_item(pq, pq.question)
            for pq in sorted_pqs
        ]

        answered_count = sum(1 for q in sorted_pqs if q.is_answered)
        correct_count = sum(1 for q in sorted_pqs if q.is_correct is True)

        # Current question is the first unanswered question
        current_item = next(
            (item for item in question_items if not item.is_answered),
            question_items[0] if question_items else None,
        )

        return MathPracticeSessionResponse(
            id=session.id,
            status=session.status,
            domain=session.domain,
            difficulty=session.difficulty,
            skill=session.skill,
            total_questions=session.total_questions,
            current_question_index=session.current_question_index,
            answered_count=answered_count,
            correct_count=correct_count,
            started_at=session.started_at,
            completed_at=session.completed_at,
            current_question=current_item,
            questions=question_items,
        )

    @staticmethod
    async def start_practice_session(
        db: AsyncSession,
        user_id: uuid.UUID,
        req: MathPracticeStartRequest,
    ) -> MathPracticeSessionResponse:
        """
        Starts a new math practice session or resumes an existing IN_PROGRESS session
        if matching parameters, avoiding duplicate questions.
        """
        # 1. Check for active session
        stmt = (
            select(MathPracticeSession)
            .where(
                MathPracticeSession.user_id == user_id,
                MathPracticeSession.status == MathPracticeSessionStatus.IN_PROGRESS.value,
            )
            .options(
                selectinload(MathPracticeSession.questions)
                .selectinload(MathPracticeQuestion.question)
                .selectinload(Question.options)
            )
            .order_by(MathPracticeSession.created_at.desc())
        )
        existing_res = await db.execute(stmt)
        active_session = existing_res.scalar_one_or_none()

        if active_session:
            # If active session exists with same configuration, resume it
            clean_dom = req.domain.upper() if req.domain and req.domain != "ALL" else None
            clean_diff = req.difficulty.upper() if req.difficulty and req.difficulty != "MIXED" else None
            clean_skill = normalize_skill(req.skill) if req.skill else None

            if (
                active_session.domain == clean_dom
                and active_session.difficulty == clean_diff
                and active_session.skill == clean_skill
            ):
                logger.info(f"Resuming active practice session {active_session.id} for user {user_id}")
                return MathPracticeService._format_session_response(active_session)
            else:
                # Mark previous active session as abandoned to start fresh
                active_session.status = MathPracticeSessionStatus.ABANDONED.value
                await db.flush()

        # 2. Select questions
        query = (
            select(Question)
            .where(
                Question.subject == Subject.MATH.value,
                Question.status == QuestionStatus.PUBLISHED.value,
            )
            .options(selectinload(Question.options))
        )

        clean_dom = req.domain.upper() if req.domain and req.domain != "ALL" else None
        if clean_dom:
            query = query.where(Question.domain == clean_dom)

        clean_diff = req.difficulty.upper() if req.difficulty and req.difficulty != "MIXED" else None
        if clean_diff:
            query = query.where(Question.difficulty == clean_diff)

        clean_skill = normalize_skill(req.skill) if req.skill else None
        if clean_skill:
            query = query.where(Question.skill == clean_skill)

        # Order randomly
        query = query.order_by(func.random()).limit(req.question_count)
        res = await db.execute(query)
        selected_questions = list(res.scalars().all())

        # Fallback if filters were too restrictive
        if len(selected_questions) < req.question_count and clean_diff:
            fallback_query = (
                select(Question)
                .where(
                    Question.subject == Subject.MATH.value,
                    Question.status == QuestionStatus.PUBLISHED.value,
                )
                .options(selectinload(Question.options))
            )
            if clean_dom:
                fallback_query = fallback_query.where(Question.domain == clean_dom)
            fallback_query = fallback_query.order_by(func.random()).limit(req.question_count)
            fallback_res = await db.execute(fallback_query)
            selected_questions = list(fallback_res.scalars().all())

        if not selected_questions:
            # Fallback to any Math questions
            generic_query = (
                select(Question)
                .where(
                    Question.subject == Subject.MATH.value,
                    Question.status == QuestionStatus.PUBLISHED.value,
                )
                .options(selectinload(Question.options))
                .order_by(func.random())
                .limit(req.question_count)
            )
            generic_res = await db.execute(generic_query)
            selected_questions = list(generic_res.scalars().all())

        if not selected_questions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No questions available for math practice session.",
            )

        now = datetime.now(timezone.utc)
        new_session = MathPracticeSession(
            user_id=user_id,
            domain=clean_dom,
            difficulty=clean_diff,
            skill=clean_skill,
            total_questions=len(selected_questions),
            current_question_index=0,
            status=MathPracticeSessionStatus.IN_PROGRESS.value,
            started_at=now,
        )
        db.add(new_session)
        await db.flush()

        for idx, q in enumerate(selected_questions):
            pq = MathPracticeQuestion(
                session_id=new_session.id,
                question_id=q.id,
                order_index=idx,
                is_answered=False,
            )
            db.add(pq)

        await db.commit()

        # Re-fetch fully loaded session
        return await MathPracticeService.get_session_by_id(db, user_id, new_session.id)

    @staticmethod
    async def get_current_session(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Optional[MathPracticeSessionResponse]:
        """Fetch current active IN_PROGRESS session if one exists."""
        stmt = (
            select(MathPracticeSession)
            .where(
                MathPracticeSession.user_id == user_id,
                MathPracticeSession.status == MathPracticeSessionStatus.IN_PROGRESS.value,
            )
            .options(
                selectinload(MathPracticeSession.questions)
                .selectinload(MathPracticeQuestion.question)
                .selectinload(Question.options)
            )
            .order_by(MathPracticeSession.created_at.desc())
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            return None
        return MathPracticeService._format_session_response(session)

    @staticmethod
    async def get_session_by_id(
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> MathPracticeSessionResponse:
        """Fetch session by ID with security checks."""
        stmt = (
            select(MathPracticeSession)
            .where(MathPracticeSession.id == session_id)
            .options(
                selectinload(MathPracticeSession.questions)
                .selectinload(MathPracticeQuestion.question)
                .selectinload(Question.options)
            )
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found.",
            )
        return MathPracticeService._format_session_response(session)

    @staticmethod
    async def submit_answer(
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        practice_question_id: uuid.UUID,
        req: MathPracticeAnswerRequest,
    ) -> MathPracticeAnswerResponse:
        """
        Submits answer for a practice question in the session:
        - Validates session ownership & state
        - Validates option belongs to the question
        - Records QuestionAttempt for user telemetry
        - Updates question status & session progress
        - Returns immediate explanation, hint, SAT shortcut, and correct answer
        """
        # 1. Fetch practice question
        stmt = (
            select(MathPracticeQuestion)
            .where(MathPracticeQuestion.id == practice_question_id)
            .options(
                selectinload(MathPracticeQuestion.session),
                selectinload(MathPracticeQuestion.question).selectinload(Question.options),
            )
        )
        res = await db.execute(stmt)
        pq = res.scalar_one_or_none()

        if not pq or pq.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice question not found in this session.",
            )

        session = pq.session
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found.",
            )

        if session.status != MathPracticeSessionStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is no longer active.",
            )

        if pq.is_answered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question has already been answered.",
            )

        q = pq.question
        # 2. Validate selected option
        chosen_opt = next((o for o in q.options if o.id == req.selected_option_id), None)
        if not chosen_opt:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Selected option does not belong to this question.",
            )

        correct_opt = next((o for o in q.options if o.is_correct), None)
        if not correct_opt:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Question has no designated correct option.",
            )

        is_correct = chosen_opt.is_correct
        now = datetime.now(timezone.utc)

        # 3. Create persistent QuestionAttempt
        attempt = QuestionAttempt(
            user_id=user_id,
            question_id=q.id,
            selected_option_id=chosen_opt.id,
            is_correct=is_correct,
            time_spent_seconds=req.time_spent_seconds,
        )
        db.add(attempt)
        await db.flush()

        # 4. Update MathPracticeQuestion
        pq.is_answered = True
        pq.is_correct = is_correct
        pq.selected_option_id = chosen_opt.id
        pq.attempt_id = attempt.id
        pq.time_spent_seconds = req.time_spent_seconds
        pq.answered_at = now

        # Automatic capture in Mistake Book if incorrect
        if not is_correct:
            await MistakeBookService.record_or_update_mistake(
                db=db,
                user_id=user_id,
                question_id=q.id,
                attempt_id=attempt.id,
                subject=q.subject,
                domain=q.domain,
                skill=q.skill,
                time_spent_seconds=req.time_spent_seconds,
                estimated_time_seconds=q.estimated_time_seconds,
            )

        # 5. Check if all questions in session are answered
        all_pqs_stmt = select(MathPracticeQuestion).where(
            MathPracticeQuestion.session_id == session.id
        )
        all_pqs_res = await db.execute(all_pqs_stmt)
        all_pqs = all_pqs_res.scalars().all()

        unanswered = [item for item in all_pqs if not item.is_answered and item.id != pq.id]
        session_completed = len(unanswered) == 0

        if session_completed:
            session.status = MathPracticeSessionStatus.COMPLETED.value
            session.completed_at = now
            session.current_question_index = len(all_pqs) - 1
        else:
            # Advance to next unanswered question index
            next_q = min(unanswered, key=lambda x: x.order_index)
            session.current_question_index = next_q.order_index

        await db.commit()

        return MathPracticeAnswerResponse(
            is_correct=is_correct,
            selected_option_id=chosen_opt.id,
            correct_option_id=correct_opt.id,
            explanation=q.explanation,
            hint=q.hint,
            sat_shortcut=q.sat_shortcut,
            session_completed=session_completed,
            next_question_index=session.current_question_index,
        )

    @staticmethod
    async def get_session_result(
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> MathPracticeResultResponse:
        """Fetch complete summary results for a practice session."""
        stmt = (
            select(MathPracticeSession)
            .where(MathPracticeSession.id == session_id)
            .options(
                selectinload(MathPracticeSession.questions)
                .selectinload(MathPracticeQuestion.question)
                .selectinload(Question.options)
            )
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found.",
            )

        sorted_pqs = sorted(session.questions, key=lambda p: p.order_index)
        total_q = len(sorted_pqs)
        answered_q = sum(1 for q in sorted_pqs if q.is_answered)
        correct_q = sum(1 for q in sorted_pqs if q.is_correct is True)
        total_time = sum(q.time_spent_seconds for q in sorted_pqs)
        accuracy = round((correct_q / float(answered_q)) * 100, 1) if answered_q > 0 else 0.0

        domain_breakdown: Dict[str, Dict] = {}
        for pq in sorted_pqs:
            dom = pq.question.domain
            if dom not in domain_breakdown:
                domain_breakdown[dom] = {"total": 0, "correct": 0, "accuracy": 0.0}
            domain_breakdown[dom]["total"] += 1
            if pq.is_correct:
                domain_breakdown[dom]["correct"] += 1

        for dom, data in domain_breakdown.items():
            if data["total"] > 0:
                data["accuracy"] = round((data["correct"] / float(data["total"])) * 100, 1)

        question_items = [
            MathPracticeService._format_question_item(pq, pq.question)
            for pq in sorted_pqs
        ]

        return MathPracticeResultResponse(
            session_id=session.id,
            domain=session.domain,
            difficulty=session.difficulty,
            skill=session.skill,
            total_questions=total_q,
            answered_questions=answered_q,
            correct_count=correct_q,
            accuracy_percentage=accuracy,
            total_time_seconds=total_time,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            domain_breakdown=domain_breakdown,
            questions=question_items,
        )
