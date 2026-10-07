from datetime import datetime, timezone
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import cast, func, Integer, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.desmos import (
    DesmosPracticeQuestion,
    DesmosPracticeSession,
    DesmosTechnique,
    QuestionDesmosTechnique,
)
from backend.app.models.enums import (
    DesmosSessionStatus,
    DesmosTechniqueType,
    Subject,
)
from backend.app.models.question import Question, QuestionAttempt, QuestionOption
from backend.app.schemas.desmos import (
    DesmosAnalyticsResponse,
    DesmosAnswerRequest,
    DesmosAnswerResponse,
    DesmosOptionSchema,
    DesmosQuestionItem,
    DesmosSessionResponse,
    DesmosSessionStartRequest,
    DesmosTechniqueDetailResponse,
    DesmosTechniqueListResponse,
    DesmosTechniqueResponse,
    ExampleQuestionResponse,
    TechniqueAnalyticsItem,
)
from backend.app.services.mistake_book_service import MistakeBookService


class DesmosService:
    @staticmethod
    def _build_question_item(
        pq: DesmosPracticeQuestion,
        technique: Optional[DesmosTechnique] = None,
    ) -> DesmosQuestionItem:
        q = pq.question
        if not q.desmos_allowed:
            rec_status = "FORBIDDEN"
            rec_reason = "Desmos calculator is not permitted for this question."
        elif q.desmos_recommended:
            rec_status = "RECOMMENDED"
            rec_reason = "Desmos is likely the fastest method for this question."
        else:
            rec_status = "ALLOWED"
            rec_reason = "Desmos can verify this answer, but manual solving may be faster."

        tech_type = pq.technique_type or (technique.technique_type if technique else None)
        tech_title = technique.title if technique else (tech_type.replace("_", " ").title() if tech_type else None)
        tech_slug = technique.slug if technique else None

        opts = [
            DesmosOptionSchema(id=o.id, label=o.label, text=o.text)
            for o in sorted(q.options, key=lambda x: x.order_index)
        ]

        return DesmosQuestionItem(
            id=pq.id,
            question_id=q.id,
            order_index=pq.order_index,
            domain=q.domain,
            skill=q.skill,
            difficulty=q.difficulty,
            question_text=q.question_text,
            estimated_time_seconds=q.estimated_time_seconds,
            desmos_allowed=q.desmos_allowed,
            desmos_recommended=q.desmos_recommended,
            technique_type=tech_type,
            technique_title=tech_title,
            technique_slug=tech_slug,
            recommendation_status=rec_status,
            recommendation_reason=rec_reason,
            options=opts,
            is_answered=pq.is_answered,
            is_correct=pq.is_correct,
            selected_option_id=pq.selected_option_id,
            time_spent_seconds=pq.time_spent_seconds,
            desmos_used=pq.desmos_used,
        )

    @classmethod
    def _format_session_response(
        cls,
        session: DesmosPracticeSession,
    ) -> DesmosSessionResponse:
        questions_formatted: List[DesmosQuestionItem] = []
        for pq in session.questions:
            questions_formatted.append(
                cls._build_question_item(pq, session.technique)
            )

        current_q = next(
            (q for q in questions_formatted if not q.is_answered),
            None,
        )

        acc = (
            round((session.correct_count / session.completed_count) * 100.0, 1)
            if session.completed_count > 0
            else 0.0
        )

        return DesmosSessionResponse(
            id=session.id,
            status=session.status,
            technique_slug=session.technique.slug if session.technique else None,
            technique_title=session.technique.title if session.technique else None,
            difficulty=session.difficulty,
            target_count=session.target_count,
            completed_count=session.completed_count,
            correct_count=session.correct_count,
            accuracy_percent=acc,
            current_question=current_q,
            questions=questions_formatted,
            started_at=session.started_at,
            completed_at=session.completed_at,
        )

    @staticmethod
    async def list_techniques(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> DesmosTechniqueListResponse:
        """List all Desmos techniques with user practice telemetry."""
        stmt = select(DesmosTechnique).order_by(DesmosTechnique.difficulty.asc(), DesmosTechnique.title.asc())
        res = await db.execute(stmt)
        techniques = res.scalars().all()

        items: List[DesmosTechniqueResponse] = []
        for tech in techniques:
            # Count questions linked
            cnt_stmt = select(func.count(QuestionDesmosTechnique.id)).where(
                QuestionDesmosTechnique.technique_id == tech.id
            )
            q_cnt = await db.scalar(cnt_stmt) or 0

            # Telemetry for this user on this technique
            telemetry_stmt = (
                select(
                    func.count(DesmosPracticeQuestion.id),
                    func.sum(cast(DesmosPracticeQuestion.is_correct, Integer)),
                )
                .join(DesmosPracticeSession, DesmosPracticeQuestion.session_id == DesmosPracticeSession.id)
                .where(
                    DesmosPracticeSession.user_id == user_id,
                    DesmosPracticeQuestion.is_answered == True,
                    (DesmosPracticeQuestion.technique_type == tech.technique_type)
                    | (DesmosPracticeSession.technique_id == tech.id),
                )
            )
            telemetry_res = await db.execute(telemetry_stmt)
            attempted, correct = telemetry_res.first() or (0, 0)
            attempted = attempted or 0
            correct = correct or 0
            acc = round((correct / attempted) * 100.0, 1) if attempted > 0 else 0.0

            items.append(
                DesmosTechniqueResponse(
                    id=tech.id,
                    slug=tech.slug,
                    title=tech.title,
                    description=tech.description,
                    technique_type=tech.technique_type,
                    subject=tech.subject,
                    difficulty=tech.difficulty,
                    when_to_use=tech.when_to_use,
                    when_not_to_use=tech.when_not_to_use,
                    sat_tip=tech.sat_tip,
                    question_count=q_cnt,
                    practiced_count=attempted,
                    accuracy_percent=acc,
                )
            )

        return DesmosTechniqueListResponse(items=items, total=len(items))

    @staticmethod
    async def get_technique_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> DesmosTechniqueDetailResponse:
        """Fetch full technique detail by slug with optional example question."""
        stmt = (
            select(DesmosTechnique)
            .where(DesmosTechnique.slug == slug)
            .options(
                selectinload(DesmosTechnique.example_question).selectinload(Question.options)
            )
        )
        res = await db.execute(stmt)
        tech = res.scalar_one_or_none()
        if not tech:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Desmos technique '{slug}' not found.",
            )

        # Count linked questions
        cnt_stmt = select(func.count(QuestionDesmosTechnique.id)).where(
            QuestionDesmosTechnique.technique_id == tech.id
        )
        q_cnt = await db.scalar(cnt_stmt) or 0

        example_resp = None
        if tech.example_question:
            eq = tech.example_question
            example_resp = ExampleQuestionResponse(
                id=eq.id,
                domain=eq.domain,
                skill=eq.skill,
                difficulty=eq.difficulty,
                question_text=eq.question_text,
                explanation=eq.explanation,
                sat_shortcut=eq.sat_shortcut,
                options=[
                    DesmosOptionSchema(id=o.id, label=o.label, text=o.text)
                    for o in sorted(eq.options, key=lambda x: x.order_index)
                ],
            )

        return DesmosTechniqueDetailResponse(
            id=tech.id,
            slug=tech.slug,
            title=tech.title,
            description=tech.description,
            technique_type=tech.technique_type,
            subject=tech.subject,
            difficulty=tech.difficulty,
            when_to_use=tech.when_to_use,
            when_not_to_use=tech.when_not_to_use,
            steps=tech.steps or [],
            common_mistakes=tech.common_mistakes or [],
            sat_tip=tech.sat_tip,
            example_question=example_resp,
            question_count=q_cnt,
        )

    @classmethod
    async def start_or_resume_session(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        req: DesmosSessionStartRequest,
    ) -> DesmosSessionResponse:
        """Start a new Desmos practice session or resume an active matching session."""
        # 1. Resolve technique if specified
        target_technique: Optional[DesmosTechnique] = None
        target_type = req.technique_type
        if req.technique_slug:
            t_stmt = select(DesmosTechnique).where(DesmosTechnique.slug == req.technique_slug)
            t_res = await db.execute(t_stmt)
            target_technique = t_res.scalar_one_or_none()
            if not target_technique:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Technique '{req.technique_slug}' not found.",
                )
            target_type = target_technique.technique_type
        elif target_type:
            t_stmt = select(DesmosTechnique).where(DesmosTechnique.technique_type == target_type)
            t_res = await db.execute(t_stmt)
            target_technique = t_res.scalar_one_or_none()

        # 2. Check for active session
        active_stmt = (
            select(DesmosPracticeSession)
            .where(
                DesmosPracticeSession.user_id == user_id,
                DesmosPracticeSession.status == DesmosSessionStatus.IN_PROGRESS.value,
            )
            .options(
                selectinload(DesmosPracticeSession.technique),
                selectinload(DesmosPracticeSession.questions)
                .selectinload(DesmosPracticeQuestion.question)
                .selectinload(Question.options),
            )
            .order_by(DesmosPracticeSession.created_at.desc())
        )
        active_res = await db.execute(active_stmt)
        active_session = active_res.scalar_one_or_none()

        if active_session:
            # Check if active session matches requested parameters
            same_tech = (
                active_session.technique_id == (target_technique.id if target_technique else None)
            )
            same_diff = active_session.difficulty == req.difficulty
            if same_tech and same_diff:
                return cls._format_session_response(active_session)
            else:
                # Mark old session abandoned
                active_session.status = DesmosSessionStatus.ABANDONED.value
                await db.flush()

        # 3. Question Selection with hierarchical fallback
        # Candidate questions must strictly have desmos_allowed == True
        selected_questions: List[Question] = []
        target_count = req.target_count

        # Strategy A: Filter by technique link
        if target_technique:
            link_q_stmt = (
                select(Question)
                .join(QuestionDesmosTechnique, Question.id == QuestionDesmosTechnique.question_id)
                .where(
                    Question.subject == Subject.MATH.value,
                    Question.desmos_allowed == True,
                    QuestionDesmosTechnique.technique_id == target_technique.id,
                )
                .options(selectinload(Question.options))
                .order_by(Question.id.asc())
            )
            if req.recommended_only:
                link_q_stmt = link_q_stmt.where(Question.desmos_recommended == True)
            if req.difficulty:
                link_q_stmt = link_q_stmt.where(Question.difficulty == req.difficulty)

            link_res = await db.execute(link_q_stmt)
            linked_candidates = link_res.scalars().all()
            for q in linked_candidates:
                if q not in selected_questions:
                    selected_questions.append(q)
                if len(selected_questions) >= target_count:
                    break

        # Strategy B: Fallback - any math questions where desmos_recommended == True
        if len(selected_questions) < target_count:
            rec_stmt = (
                select(Question)
                .where(
                    Question.subject == Subject.MATH.value,
                    Question.desmos_allowed == True,
                    Question.desmos_recommended == True,
                )
                .options(selectinload(Question.options))
                .order_by(Question.id.asc())
            )
            if req.difficulty:
                rec_stmt = rec_stmt.where(Question.difficulty == req.difficulty)

            rec_res = await db.execute(rec_stmt)
            for q in rec_res.scalars().all():
                if q not in selected_questions:
                    selected_questions.append(q)
                if len(selected_questions) >= target_count:
                    break

        # Strategy C: Fallback - any math questions where desmos_allowed == True
        if len(selected_questions) < target_count:
            all_stmt = (
                select(Question)
                .where(
                    Question.subject == Subject.MATH.value,
                    Question.desmos_allowed == True,
                )
                .options(selectinload(Question.options))
                .order_by(Question.id.asc())
            )
            all_res = await db.execute(all_stmt)
            for q in all_res.scalars().all():
                if q not in selected_questions:
                    selected_questions.append(q)
                if len(selected_questions) >= target_count:
                    break

        if not selected_questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions available for Desmos practice.",
            )

        # 4. Create new DesmosPracticeSession
        session = DesmosPracticeSession(
            user_id=user_id,
            technique_id=target_technique.id if target_technique else None,
            technique_type=target_type,
            difficulty=req.difficulty,
            target_count=len(selected_questions),
            completed_count=0,
            correct_count=0,
            status=DesmosSessionStatus.IN_PROGRESS.value,
        )
        db.add(session)
        await db.flush()

        for idx, q in enumerate(selected_questions):
            pq = DesmosPracticeQuestion(
                session_id=session.id,
                question_id=q.id,
                order_index=idx,
                technique_type=target_type or (
                    DesmosTechniqueType.INTERSECTION.value if q.desmos_recommended else DesmosTechniqueType.VERIFICATION.value
                ),
                is_answered=False,
            )
            db.add(pq)

        await db.commit()

        # Reload with relations
        return await cls.get_session_by_id(db, user_id, session.id)

    @classmethod
    async def get_current_session(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Optional[DesmosSessionResponse]:
        """Fetch user's current IN_PROGRESS session."""
        stmt = (
            select(DesmosPracticeSession)
            .where(
                DesmosPracticeSession.user_id == user_id,
                DesmosPracticeSession.status == DesmosSessionStatus.IN_PROGRESS.value,
            )
            .options(
                selectinload(DesmosPracticeSession.technique),
                selectinload(DesmosPracticeSession.questions)
                .selectinload(DesmosPracticeQuestion.question)
                .selectinload(Question.options),
            )
            .order_by(DesmosPracticeSession.created_at.desc())
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            return None
        return cls._format_session_response(session)

    @classmethod
    async def get_session_by_id(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> DesmosSessionResponse:
        """Fetch session by ID with security isolation."""
        stmt = (
            select(DesmosPracticeSession)
            .where(DesmosPracticeSession.id == session_id)
            .options(
                selectinload(DesmosPracticeSession.technique),
                selectinload(DesmosPracticeSession.questions)
                .selectinload(DesmosPracticeQuestion.question)
                .selectinload(Question.options),
            )
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Desmos practice session not found.",
            )
        return cls._format_session_response(session)

    @classmethod
    async def submit_answer(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        req: DesmosAnswerRequest,
    ) -> DesmosAnswerResponse:
        """Submit an answer to a practice question in a Desmos session."""
        # 1. Fetch practice question
        stmt = (
            select(DesmosPracticeQuestion)
            .where(
                DesmosPracticeQuestion.session_id == session_id,
                DesmosPracticeQuestion.question_id == question_id,
            )
            .options(
                selectinload(DesmosPracticeQuestion.session).selectinload(DesmosPracticeSession.technique),
                selectinload(DesmosPracticeQuestion.question).selectinload(Question.options),
            )
        )
        res = await db.execute(stmt)
        pq = res.scalar_one_or_none()

        if not pq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found in this practice session.",
            )

        session = pq.session
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found.",
            )

        if session.status != DesmosSessionStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Practice session is not active.",
            )

        if pq.is_answered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This question has already been answered.",
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

        # 3. Create QuestionAttempt
        attempt = QuestionAttempt(
            user_id=user_id,
            question_id=q.id,
            selected_option_id=chosen_opt.id,
            is_correct=is_correct,
            time_spent_seconds=req.time_spent_seconds,
        )
        db.add(attempt)
        await db.flush()

        # 4. Update DesmosPracticeQuestion
        pq.is_answered = True
        pq.is_correct = is_correct
        pq.selected_option_id = chosen_opt.id
        pq.attempt_id = attempt.id
        pq.time_spent_seconds = req.time_spent_seconds
        pq.desmos_used = req.desmos_used
        pq.answered_at = now

        # 5. Update Session telemetry
        session.completed_count += 1
        if is_correct:
            session.correct_count += 1

        # Check completion
        is_completed = session.completed_count >= session.target_count
        if is_completed:
            session.status = DesmosSessionStatus.COMPLETED.value
            session.completed_at = now

        # 6. Mistake Book synchronization if incorrect
        if not is_correct:
            try:
                await MistakeBookService.record_or_update_mistake(
                    db=db,
                    user_id=user_id,
                    question_id=q.id,
                    attempt_id=attempt.id,
                    subject=q.subject,
                    domain=q.domain,
                    skill=q.skill,
                )
            except Exception:
                pass

        await db.commit()

        # 7. Formulate guidance & next question
        acc = round((session.correct_count / session.completed_count) * 100.0, 1)

        # Find next question id
        next_pq_stmt = (
            select(DesmosPracticeQuestion.question_id)
            .where(
                DesmosPracticeQuestion.session_id == session.id,
                DesmosPracticeQuestion.is_answered == False,
            )
            .order_by(DesmosPracticeQuestion.order_index.asc())
        )
        next_q_res = await db.execute(next_pq_stmt)
        next_qid = next_q_res.scalars().first()

        desmos_guidance = None
        if session.technique:
            desmos_guidance = f"Desmos Strategy ({session.technique.title}): {session.technique.sat_tip}"
        elif q.sat_shortcut:
            desmos_guidance = q.sat_shortcut

        return DesmosAnswerResponse(
            is_correct=is_correct,
            correct_option_id=correct_opt.id,
            explanation=q.explanation,
            hint=q.hint,
            sat_shortcut=q.sat_shortcut,
            desmos_guidance=desmos_guidance,
            session_completed=is_completed,
            session_accuracy=acc,
            next_question_id=next_qid,
        )

    @classmethod
    async def abandon_session(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> DesmosSessionResponse:
        """Mark an active session as abandoned."""
        stmt = (
            select(DesmosPracticeSession)
            .where(DesmosPracticeSession.id == session_id)
            .options(
                selectinload(DesmosPracticeSession.technique),
                selectinload(DesmosPracticeSession.questions)
                .selectinload(DesmosPracticeQuestion.question)
                .selectinload(Question.options),
            )
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session or session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Desmos practice session not found.",
            )

        if session.status == DesmosSessionStatus.IN_PROGRESS.value:
            session.status = DesmosSessionStatus.ABANDONED.value
            await db.commit()

        return cls._format_session_response(session)

    @staticmethod
    async def get_user_desmos_analytics(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> DesmosAnalyticsResponse:
        """Aggregate user Desmos practice metrics and technique breakdown."""
        # 1. Overall stats
        overall_stmt = (
            select(
                func.count(DesmosPracticeQuestion.id),
                func.sum(cast(DesmosPracticeQuestion.is_correct, Integer)),
                func.avg(DesmosPracticeQuestion.time_spent_seconds),
            )
            .join(DesmosPracticeSession, DesmosPracticeQuestion.session_id == DesmosPracticeSession.id)
            .where(
                DesmosPracticeSession.user_id == user_id,
                DesmosPracticeQuestion.is_answered == True,
            )
        )
        overall_res = await db.execute(overall_stmt)
        total_att, total_cor, avg_time = overall_res.first() or (0, 0, 0.0)
        total_att = total_att or 0
        total_cor = total_cor or 0
        avg_time = round(float(avg_time or 0.0), 1)
        overall_acc = round((total_cor / total_att) * 100.0, 1) if total_att > 0 else 0.0

        # 2. Recommended vs Allowed breakdown
        rec_stmt = (
            select(
                func.count(DesmosPracticeQuestion.id),
            )
            .join(DesmosPracticeSession, DesmosPracticeQuestion.session_id == DesmosPracticeSession.id)
            .join(Question, DesmosPracticeQuestion.question_id == Question.id)
            .where(
                DesmosPracticeSession.user_id == user_id,
                DesmosPracticeQuestion.is_answered == True,
                Question.desmos_recommended == True,
            )
        )
        rec_cnt = await db.scalar(rec_stmt) or 0
        allowed_cnt = total_att - rec_cnt

        # 3. Technique breakdown
        techniques_stmt = select(DesmosTechnique).order_by(DesmosTechnique.title.asc())
        t_res = await db.execute(techniques_stmt)
        all_techniques = t_res.scalars().all()

        technique_items: List[TechniqueAnalyticsItem] = []
        for tech in all_techniques:
            tech_stmt = (
                select(
                    func.count(DesmosPracticeQuestion.id),
                    func.sum(cast(DesmosPracticeQuestion.is_correct, Integer)),
                    func.avg(DesmosPracticeQuestion.time_spent_seconds),
                )
                .join(DesmosPracticeSession, DesmosPracticeQuestion.session_id == DesmosPracticeSession.id)
                .where(
                    DesmosPracticeSession.user_id == user_id,
                    DesmosPracticeQuestion.is_answered == True,
                    (DesmosPracticeQuestion.technique_type == tech.technique_type)
                    | (DesmosPracticeSession.technique_id == tech.id),
                )
            )
            t_data = await db.execute(tech_stmt)
            p_cnt, c_cnt, t_time = t_data.first() or (0, 0, 0.0)
            p_cnt = p_cnt or 0
            c_cnt = c_cnt or 0
            t_acc = round((c_cnt / p_cnt) * 100.0, 1) if p_cnt > 0 else 0.0
            t_avg = round(float(t_time or 0.0), 1)

            technique_items.append(
                TechniqueAnalyticsItem(
                    technique_type=tech.technique_type,
                    technique_slug=tech.slug,
                    technique_title=tech.title,
                    practiced_count=p_cnt,
                    correct_count=c_cnt,
                    accuracy_percent=t_acc,
                    avg_time_seconds=t_avg,
                )
            )

        return DesmosAnalyticsResponse(
            total_questions_attempted=total_att,
            total_correct=total_cor,
            overall_accuracy=overall_acc,
            avg_time_seconds=avg_time,
            recommended_count=rec_cnt,
            allowed_count=allowed_cnt,
            techniques=technique_items,
        )
