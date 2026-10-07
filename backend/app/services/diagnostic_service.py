from datetime import datetime, timezone
from typing import Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.core.logging import logger
from backend.app.models.diagnostic import (
    DiagnosticModule,
    DiagnosticQuestion,
    DiagnosticResult,
    DiagnosticSession,
)
from backend.app.models.enums import (
    DiagnosticModuleStatus,
    DiagnosticStatus,
    Subject,
)
from backend.app.models.profile import UserProfile
from backend.app.models.question import Question, QuestionAttempt, QuestionOption
from backend.app.schemas.diagnostic import (
    CurrentDiagnosticResponse,
    DiagnosticAnswerResponse,
    DiagnosticResultResponse,
    DiagnosticSessionResponse,
)
from backend.app.schemas.question import QuestionPublic
from backend.app.services.diagnostic_question_selector import DiagnosticQuestionSelector
from backend.app.services.diagnostic_result_service import DiagnosticResultService
from backend.app.services.mistake_book_service import MistakeBookService


class DiagnosticService:
    async def start_or_resume(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> DiagnosticSessionResponse:
        """
        Starts a new 40-question diagnostic session or resumes an existing IN_PROGRESS session.
        Enforces one active diagnostic per user.
        """
        # 1. Check for existing active session
        stmt = (
            select(DiagnosticSession)
            .where(
                DiagnosticSession.user_id == user_id,
                DiagnosticSession.status == DiagnosticStatus.IN_PROGRESS.value,
            )
            .order_by(DiagnosticSession.created_at.desc())
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            logger.info(f"Resuming active diagnostic session {existing.id} for user {user_id}")
            return DiagnosticSessionResponse(
                id=existing.id,
                status=existing.status,
                current_module=existing.current_module,
                current_question_index=existing.current_question_index,
                started_at=existing.started_at,
                total_questions=40,
            )

        # 2. Select 20 Math and 20 RW questions
        try:
            math_questions, rw_questions = await DiagnosticQuestionSelector.select_questions(db)
        except ValueError as err:
            logger.error(f"Failed to assemble diagnostic questions: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(err),
            )

        now = datetime.now(timezone.utc)

        # 3. Create Diagnostic Session
        session = DiagnosticSession(
            user_id=user_id,
            status=DiagnosticStatus.IN_PROGRESS.value,
            current_module=Subject.MATH.value,
            current_question_index=0,
            started_at=now,
        )
        db.add(session)
        await db.flush()

        # 4. Create Module 1 (Math)
        mod_math = DiagnosticModule(
            session_id=session.id,
            subject=Subject.MATH.value,
            module_number=1,
            status=DiagnosticModuleStatus.IN_PROGRESS.value,
            started_at=now,
        )
        db.add(mod_math)
        await db.flush()

        # 5. Create Module 2 (Reading & Writing)
        mod_rw = DiagnosticModule(
            session_id=session.id,
            subject=Subject.READING_WRITING.value,
            module_number=2,
            status=DiagnosticModuleStatus.NOT_STARTED.value,
        )
        db.add(mod_rw)
        await db.flush()

        # 6. Assign questions for Module 1
        for idx, q in enumerate(math_questions):
            dq = DiagnosticQuestion(
                module_id=mod_math.id,
                question_id=q.id,
                order_index=idx,
            )
            db.add(dq)

        # 7. Assign questions for Module 2
        for idx, q in enumerate(rw_questions):
            dq = DiagnosticQuestion(
                module_id=mod_rw.id,
                question_id=q.id,
                order_index=idx,
            )
            db.add(dq)

        # 8. Update UserProfile status
        profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        prof_res = await db.execute(profile_stmt)
        profile = prof_res.scalar_one_or_none()
        if profile and profile.diagnostic_status != "completed":
            profile.diagnostic_status = "in_progress"

        await db.commit()
        await db.refresh(session)

        logger.info(f"Created new diagnostic session {session.id} for user {user_id}")
        return DiagnosticSessionResponse(
            id=session.id,
            status=session.status,
            current_module=session.current_module,
            current_question_index=session.current_question_index,
            started_at=session.started_at,
            total_questions=40,
        )

    async def get_current_diagnostic(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Optional[CurrentDiagnosticResponse]:
        """
        Retrieves current active diagnostic session and next question to be answered.
        Uses safe public question format with strict answer key withholding.
        """
        stmt = (
            select(DiagnosticSession)
            .where(
                DiagnosticSession.user_id == user_id,
                DiagnosticSession.status == DiagnosticStatus.IN_PROGRESS.value,
            )
            .options(
                selectinload(DiagnosticSession.modules)
                .selectinload(DiagnosticModule.questions)
                .selectinload(DiagnosticQuestion.question)
                .selectinload(Question.options),
                selectinload(DiagnosticSession.modules)
                .selectinload(DiagnosticModule.questions)
                .selectinload(DiagnosticQuestion.question)
                .selectinload(Question.passage),
            )
            .order_by(DiagnosticSession.created_at.desc())
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            return None

        # Determine active module
        active_mod = next(
            (m for m in session.modules if m.status == DiagnosticModuleStatus.IN_PROGRESS.value),
            None,
        )
        if not active_mod:
            active_mod = session.modules[0] if session.modules else None

        if not active_mod:
            return None

        questions_in_mod = sorted(active_mod.questions, key=lambda q: q.order_index)
        answered_in_mod = sum(1 for q in questions_in_mod if q.is_answered)
        total_in_mod = len(questions_in_mod)

        total_answered_overall = sum(
            1 for m in session.modules for q in m.questions if q.is_answered
        )
        total_overall = 40
        progress_pct = int((total_answered_overall / float(total_overall)) * 100)

        # Find first unanswered question in active module
        next_dq = next((q for q in questions_in_mod if not q.is_answered), None)
        current_question_public = None
        current_q_idx = answered_in_mod

        if next_dq:
            current_q_idx = next_dq.order_index
            current_question_public = QuestionPublic.model_validate(next_dq.question)

        return CurrentDiagnosticResponse(
            id=session.id,
            status=session.status,
            subject=active_mod.subject,
            module_number=active_mod.module_number,
            current_question_index=current_q_idx,
            answered_in_module=answered_in_mod,
            total_in_module=total_in_mod,
            total_answered=total_answered_overall,
            total_questions=total_overall,
            progress_percent=progress_pct,
            current_question=current_question_public,
        )

    async def submit_answer(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        diagnostic_id: uuid.UUID,
        question_id: uuid.UUID,
        selected_option_id: uuid.UUID,
        time_spent_seconds: int,
    ) -> DiagnosticAnswerResponse:
        """
        Submits answer for an assigned diagnostic question.
        Ensures idempotency, validates cross-question option tampering,
        and manages module / session completion.
        """
        if time_spent_seconds < 0 or time_spent_seconds > 3600:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Time spent must be between 0 and 3600 seconds.",
            )

        # 1. Fetch diagnostic session
        stmt = (
            select(DiagnosticSession)
            .where(DiagnosticSession.id == diagnostic_id)
            .options(
                selectinload(DiagnosticSession.modules)
                .selectinload(DiagnosticModule.questions)
                .selectinload(DiagnosticQuestion.question),
            )
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnostic session not found.",
            )

        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this diagnostic session.",
            )

        if session.status != DiagnosticStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Diagnostic session is not in progress (current status: {session.status}).",
            )

        # 2. Find active module
        active_mod = next(
            (m for m in session.modules if m.status == DiagnosticModuleStatus.IN_PROGRESS.value),
            None,
        )
        if not active_mod:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active module found in this diagnostic session.",
            )

        # 3. Find question assignment in active module
        target_dq = next(
            (dq for dq in active_mod.questions if dq.question_id == question_id),
            None,
        )
        if not target_dq:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question does not belong to the current active diagnostic module.",
            )

        if target_dq.is_answered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This diagnostic question has already been answered.",
            )

        # 4. Verify option belongs to the question
        opt_stmt = select(QuestionOption).where(QuestionOption.id == selected_option_id)
        opt_res = await db.execute(opt_stmt)
        option = opt_res.scalar_one_or_none()

        if not option:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected option not found.",
            )

        if option.question_id != question_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected option does not belong to the specified question.",
            )

        now = datetime.now(timezone.utc)
        is_correct = bool(option.is_correct)

        # 5. Create QuestionAttempt
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

        # 6. Update DiagnosticQuestion assignment
        target_dq.selected_option_id = selected_option_id
        target_dq.attempt_id = attempt.id
        target_dq.is_answered = True
        target_dq.is_correct = is_correct
        target_dq.time_spent_seconds = time_spent_seconds
        target_dq.answered_at = now

        # 7. Check module and session progression
        unanswered_remaining = [
            dq for dq in active_mod.questions if not dq.is_answered and dq.id != target_dq.id
        ]

        module_completed = False
        diagnostic_completed = False

        if len(unanswered_remaining) == 0:
            # Active module complete
            active_mod.status = DiagnosticModuleStatus.COMPLETED.value
            active_mod.completed_at = now
            module_completed = True

            if active_mod.module_number == 1:
                # Transition to Module 2 (Reading & Writing)
                mod2 = next((m for m in session.modules if m.module_number == 2), None)
                if mod2:
                    mod2.status = DiagnosticModuleStatus.IN_PROGRESS.value
                    mod2.started_at = now
                    session.current_module = Subject.READING_WRITING.value
                    session.current_question_index = 0
            else:
                # Module 2 completed -> Entire test finished!
                session.status = DiagnosticStatus.COMPLETED.value
                session.completed_at = now
                diagnostic_completed = True
                await db.flush()
                # Compute & persist result
                await DiagnosticResultService.create_and_store_result(db, session)

                # Automatically populate Mistake Book with incorrect answers from Diagnostic
                for m in session.modules:
                    for dq in m.questions:
                        if dq.is_answered and dq.is_correct is False and dq.question:
                            await MistakeBookService.record_or_update_mistake(
                                db=db,
                                user_id=session.user_id,
                                question_id=dq.question_id,
                                attempt_id=dq.attempt_id,
                                subject=dq.question.subject,
                                domain=dq.question.domain,
                                skill=dq.question.skill,
                                time_spent_seconds=dq.time_spent_seconds,
                                estimated_time_seconds=dq.question.estimated_time_seconds,
                            )

        else:
            session.current_question_index = target_dq.order_index + 1

        total_answered_overall = sum(
            1 for m in session.modules for q in m.questions if q.is_answered
        )

        await db.commit()

        return DiagnosticAnswerResponse(
            module_completed=module_completed,
            diagnostic_completed=diagnostic_completed,
            current_module=session.current_module,
            current_question_index=session.current_question_index,
            total_answered=total_answered_overall,
            total_questions=40,
        )

    async def get_result(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        diagnostic_id: uuid.UUID,
    ) -> DiagnosticResultResponse:
        """
        Retrieves calculated results for a completed diagnostic session.
        Enforces cross-user security and completion state.
        """
        stmt = (
            select(DiagnosticSession)
            .where(DiagnosticSession.id == diagnostic_id)
            .options(
                selectinload(DiagnosticSession.result),
                selectinload(DiagnosticSession.modules)
                .selectinload(DiagnosticModule.questions)
                .selectinload(DiagnosticQuestion.question),
            )
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diagnostic session not found.",
            )

        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this diagnostic result.",
            )

        if session.status != DiagnosticStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diagnostic session is not yet completed.",
            )

        res_stmt = select(DiagnosticResult).where(DiagnosticResult.session_id == diagnostic_id)
        res_exec = await db.execute(res_stmt)
        result = res_exec.scalar_one_or_none()
        if not result:
            result = await DiagnosticResultService.create_and_store_result(db, session)


        return DiagnosticResultResponse.model_validate(result)

    async def get_latest_result(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> DiagnosticResultResponse:
        """
        Retrieves the latest completed diagnostic result for the user.
        """
        stmt = (
            select(DiagnosticSession)
            .where(
                DiagnosticSession.user_id == user_id,
                DiagnosticSession.status == DiagnosticStatus.COMPLETED.value,
            )
            .options(
                selectinload(DiagnosticSession.modules)
                .selectinload(DiagnosticModule.questions)
                .selectinload(DiagnosticQuestion.question),
            )
            .order_by(DiagnosticSession.completed_at.desc(), DiagnosticSession.created_at.desc())
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No completed diagnostic tests found for this user.",
            )

        res_stmt = select(DiagnosticResult).where(DiagnosticResult.session_id == session.id)
        res_exec = await db.execute(res_stmt)
        result = res_exec.scalar_one_or_none()
        if not result:
            result = await DiagnosticResultService.create_and_store_result(db, session)

        return DiagnosticResultResponse.model_validate(result)



diagnostic_service = DiagnosticService()
