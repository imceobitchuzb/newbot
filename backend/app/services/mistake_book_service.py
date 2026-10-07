from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.core.logging import logger
from backend.app.models.enums import MistakeStatus, MistakeType
from backend.app.models.mistake_book import MistakeBookEntry
from backend.app.models.question import Question, QuestionAttempt, QuestionOption
from backend.app.schemas.mistake_book import (
    MistakeEntryItem,
    MistakeListResponse,
    MistakeRetryRequest,
    MistakeRetryResponse,
)
from backend.app.schemas.question import QuestionOptionPublic


def calculate_next_review_interval(review_count: int) -> timedelta:
    """
    Deterministic Mistake Review Schedule:
    - Review #0 (new mistake): +1 day
    - Review #1: +3 days
    - Review #2: +7 days
    - Review #3: +14 days
    - Review #4+: +30 days
    """
    if review_count <= 0:
        return timedelta(days=1)
    elif review_count == 1:
        return timedelta(days=3)
    elif review_count == 2:
        return timedelta(days=7)
    elif review_count == 3:
        return timedelta(days=14)
    else:
        return timedelta(days=30)


def normalize_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class MistakeBookService:
    @staticmethod
    def _format_entry_item(entry: MistakeBookEntry) -> MistakeEntryItem:
        """Format MistakeBookEntry with full question details and review info."""
        now = datetime.now(timezone.utc)
        entry_next = normalize_to_utc(entry.next_review_at)
        is_due = bool(entry_next and entry_next <= now)
        q = entry.question


        options_public = [
            QuestionOptionPublic(
                id=opt.id,
                label=opt.label,
                text=opt.text,
                order_index=opt.order_index,
            )
            for opt in sorted(q.options, key=lambda o: o.order_index)
        ]

        correct_opt = next((o for o in q.options if o.is_correct), None)
        last_selected_id = entry.attempt.selected_option_id if entry.attempt else None

        return MistakeEntryItem(
            id=entry.id,
            user_id=entry.user_id,
            question_id=entry.question_id,
            attempt_id=entry.attempt_id,
            subject=entry.subject,
            domain=entry.domain,
            skill=entry.skill,
            status=entry.status,
            mistake_type=entry.mistake_type,
            review_count=entry.review_count,
            correct_retry_count=entry.correct_retry_count,
            incorrect_retry_count=entry.incorrect_retry_count,
            last_reviewed_at=entry.last_reviewed_at,
            next_review_at=entry.next_review_at,
            is_due=is_due,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            question_text=q.question_text,
            difficulty=q.difficulty,
            options=options_public,
            explanation=q.explanation,
            hint=q.hint,
            sat_shortcut=q.sat_shortcut,
            correct_option_id=correct_opt.id if correct_opt else None,
            last_selected_option_id=last_selected_id,
        )

    @staticmethod
    async def record_or_update_mistake(
        db: AsyncSession,
        user_id: uuid.UUID,
        question_id: uuid.UUID,
        attempt_id: Optional[uuid.UUID],
        subject: str,
        domain: str,
        skill: str,
        time_spent_seconds: int = 0,
        estimated_time_seconds: int = 75,
    ) -> MistakeBookEntry:
        """
        Idempotent capture of an incorrect answer:
        If mistake already exists for (user_id, question_id), updates it without duplication.
        Handles regression if question was previously MASTERED.
        """
        now = datetime.now(timezone.utc)

        stmt = select(MistakeBookEntry).where(
            MistakeBookEntry.user_id == user_id,
            MistakeBookEntry.question_id == question_id,
        )
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()

        if entry:
            # Entry exists: update attempt and check regression
            entry.attempt_id = attempt_id or entry.attempt_id
            if entry.status == MistakeStatus.MASTERED.value:
                # Regressed from MASTERED back to ACTIVE
                logger.info(f"Question {question_id} regressed from MASTERED to ACTIVE for user {user_id}")
                entry.status = MistakeStatus.ACTIVE.value
                entry.next_review_at = now + timedelta(days=1)
            entry.updated_at = now
            return entry

        # Suggested deterministic classification
        suggested_type = MistakeType.UNKNOWN.value
        if time_spent_seconds > (estimated_time_seconds * 1.5):
            suggested_type = MistakeType.TIME_PRESSURE.value

        next_review = now + calculate_next_review_interval(0)

        new_entry = MistakeBookEntry(
            user_id=user_id,
            question_id=question_id,
            attempt_id=attempt_id,
            subject=subject,
            domain=domain,
            skill=skill,
            status=MistakeStatus.ACTIVE.value,
            mistake_type=suggested_type,
            review_count=0,
            correct_retry_count=0,
            incorrect_retry_count=0,
            next_review_at=next_review,
        )
        db.add(new_entry)
        await db.flush()
        return new_entry

    @staticmethod
    async def review_mistake(
        db: AsyncSession,
        user_id: uuid.UUID,
        mistake_id: uuid.UUID,
        new_mistake_type: Optional[MistakeType] = None,
    ) -> MistakeEntryItem:
        """Mark a mistake as reviewed and advance its review schedule."""
        stmt = (
            select(MistakeBookEntry)
            .where(MistakeBookEntry.id == mistake_id)
            .options(
                selectinload(MistakeBookEntry.question).selectinload(Question.options),
                selectinload(MistakeBookEntry.attempt),
            )
        )
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()

        if not entry or entry.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mistake entry not found.",
            )

        now = datetime.now(timezone.utc)
        entry.review_count += 1
        entry.last_reviewed_at = now
        entry.next_review_at = now + calculate_next_review_interval(entry.review_count)

        if entry.status == MistakeStatus.ACTIVE.value:
            entry.status = MistakeStatus.IN_REVIEW.value

        if new_mistake_type:
            entry.mistake_type = new_mistake_type.value

        await db.commit()
        await db.refresh(entry)
        return MistakeBookService._format_entry_item(entry)

    @staticmethod
    async def classify_mistake(
        db: AsyncSession,
        user_id: uuid.UUID,
        mistake_id: uuid.UUID,
        mistake_type: MistakeType,
    ) -> MistakeEntryItem:
        """Explicitly classify the mistake type (Concept Gap, Careless Error, etc.)."""
        stmt = (
            select(MistakeBookEntry)
            .where(MistakeBookEntry.id == mistake_id)
            .options(
                selectinload(MistakeBookEntry.question).selectinload(Question.options),
                selectinload(MistakeBookEntry.attempt),
            )
        )
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()

        if not entry or entry.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mistake entry not found.",
            )

        entry.mistake_type = mistake_type.value
        await db.commit()
        await db.refresh(entry)
        return MistakeBookService._format_entry_item(entry)

    @staticmethod
    async def retry_mistake(
        db: AsyncSession,
        user_id: uuid.UUID,
        mistake_id: uuid.UUID,
        req: MistakeRetryRequest,
    ) -> MistakeRetryResponse:
        """
        Execute an error remediation retry on a mistake question:
        - Validates option belongs to the question
        - Creates a NEW QuestionAttempt without mutating previous attempts
        - Implements strict Mastery criteria (>=2 retries, last 2 retries correct)
        - Implements Regression logic if wrong on previously MASTERED item
        """
        stmt = (
            select(MistakeBookEntry)
            .where(MistakeBookEntry.id == mistake_id)
            .options(
                selectinload(MistakeBookEntry.question).selectinload(Question.options),
            )
        )
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()

        if not entry or entry.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mistake entry not found.",
            )

        q = entry.question
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

        # 1. Create a NEW QuestionAttempt (preserving full historical trajectory)
        retry_attempt = QuestionAttempt(
            user_id=user_id,
            question_id=q.id,
            selected_option_id=chosen_opt.id,
            is_correct=is_correct,
            time_spent_seconds=req.time_spent_seconds,
        )
        db.add(retry_attempt)
        await db.flush()

        # Update entry pointer to newest attempt
        entry.attempt_id = retry_attempt.id
        entry.last_reviewed_at = now

        is_mastered = False

        if is_correct:
            entry.correct_retry_count += 1

            # Fetch the 2 most recent attempts on this question for user
            recent_attempts_stmt = (
                select(QuestionAttempt)
                .where(
                    QuestionAttempt.user_id == user_id,
                    QuestionAttempt.question_id == q.id,
                )
                .order_by(QuestionAttempt.answered_at.desc())
                .limit(2)
            )
            recent_res = await db.execute(recent_attempts_stmt)
            recent_attempts = list(recent_res.scalars().all())

            total_retries = entry.correct_retry_count + entry.incorrect_retry_count

            # Strict Mastery: at least 2 retries performed AND last 2 attempts were correct
            if len(recent_attempts) >= 2 and all(a.is_correct for a in recent_attempts) and total_retries >= 2:
                entry.status = MistakeStatus.MASTERED.value
                is_mastered = True
            else:
                entry.status = MistakeStatus.IN_REVIEW.value

            entry.next_review_at = now + calculate_next_review_interval(entry.review_count + 1)
        else:
            entry.incorrect_retry_count += 1
            if entry.status == MistakeStatus.MASTERED.value:
                # Regressed
                entry.status = MistakeStatus.ACTIVE.value
            entry.next_review_at = now + timedelta(days=1)

        await db.commit()

        return MistakeRetryResponse(
            is_correct=is_correct,
            selected_option_id=chosen_opt.id,
            correct_option_id=correct_opt.id,
            explanation=q.explanation,
            hint=q.hint,
            sat_shortcut=q.sat_shortcut,
            new_status=entry.status,
            correct_retry_count=entry.correct_retry_count,
            incorrect_retry_count=entry.incorrect_retry_count,
            is_mastered=is_mastered,
        )

    @staticmethod
    async def get_mistakes(
        db: AsyncSession,
        user_id: uuid.UUID,
        subject: Optional[str] = None,
        domain: Optional[str] = None,
        skill: Optional[str] = None,
        status: Optional[str] = None,
        mistake_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> MistakeListResponse:
        """Query user's mistakes with filtering and priority ordering."""
        query = (
            select(MistakeBookEntry)
            .where(MistakeBookEntry.user_id == user_id)
            .options(
                selectinload(MistakeBookEntry.question).selectinload(Question.options),
                selectinload(MistakeBookEntry.attempt),
            )
        )

        if subject:
            query = query.where(MistakeBookEntry.subject == subject.upper())
        if domain:
            query = query.where(MistakeBookEntry.domain == domain.upper())
        if skill:
            query = query.where(MistakeBookEntry.skill == skill)
        if status:
            query = query.where(MistakeBookEntry.status == status.upper())
        if mistake_type:
            query = query.where(MistakeBookEntry.mistake_type == mistake_type.upper())

        # Total count query
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar_one()

        # Priority ordering: overdue first, then ACTIVE, then updated_at desc
        now = datetime.now(timezone.utc)
        query = query.order_by(
            # Sort by due date (items past next_review_at come first)
            MistakeBookEntry.next_review_at.asc(),
            MistakeBookEntry.created_at.desc(),
        ).limit(limit).offset(offset)

        res = await db.execute(query)
        entries = list(res.scalars().all())

        items = [MistakeBookService._format_entry_item(e) for e in entries]

        return MistakeListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    async def get_mistake_by_id(
        db: AsyncSession,
        user_id: uuid.UUID,
        mistake_id: uuid.UUID,
    ) -> MistakeEntryItem:
        """Fetch detail of a single mistake entry."""
        stmt = (
            select(MistakeBookEntry)
            .where(MistakeBookEntry.id == mistake_id)
            .options(
                selectinload(MistakeBookEntry.question).selectinload(Question.options),
                selectinload(MistakeBookEntry.attempt),
            )
        )
        res = await db.execute(stmt)
        entry = res.scalar_one_or_none()

        if not entry or entry.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mistake entry not found.",
            )

        return MistakeBookService._format_entry_item(entry)

    @staticmethod
    async def get_next_priority_mistake(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Optional[MistakeEntryItem]:
        """
        Fetch the highest priority mistake to remediate:
        1. Overdue reviews (next_review_at <= now, status != MASTERED)
        2. Status ACTIVE
        3. Status IN_REVIEW
        """
        now = datetime.now(timezone.utc)

        # 1. Overdue reviews
        overdue_stmt = (
            select(MistakeBookEntry)
            .where(
                MistakeBookEntry.user_id == user_id,
                MistakeBookEntry.status.in_([MistakeStatus.ACTIVE.value, MistakeStatus.IN_REVIEW.value]),
                MistakeBookEntry.next_review_at <= now,
            )
            .options(
                selectinload(MistakeBookEntry.question).selectinload(Question.options),
                selectinload(MistakeBookEntry.attempt),
            )
            .order_by(MistakeBookEntry.next_review_at.asc())
            .limit(1)
        )
        res = await db.execute(overdue_stmt)
        entry = res.scalar_one_or_none()
        if entry:
            return MistakeBookService._format_entry_item(entry)

        # 2. ACTIVE mistakes
        active_stmt = (
            select(MistakeBookEntry)
            .where(
                MistakeBookEntry.user_id == user_id,
                MistakeBookEntry.status == MistakeStatus.ACTIVE.value,
            )
            .options(
                selectinload(MistakeBookEntry.question).selectinload(Question.options),
                selectinload(MistakeBookEntry.attempt),
            )
            .order_by(MistakeBookEntry.created_at.desc())
            .limit(1)
        )
        res = await db.execute(active_stmt)
        entry = res.scalar_one_or_none()
        if entry:
            return MistakeBookService._format_entry_item(entry)

        # 3. Any IN_REVIEW mistake
        in_review_stmt = (
            select(MistakeBookEntry)
            .where(
                MistakeBookEntry.user_id == user_id,
                MistakeBookEntry.status == MistakeStatus.IN_REVIEW.value,
            )
            .options(
                selectinload(MistakeBookEntry.question).selectinload(Question.options),
                selectinload(MistakeBookEntry.attempt),
            )
            .order_by(MistakeBookEntry.created_at.desc())
            .limit(1)
        )
        res = await db.execute(in_review_stmt)
        entry = res.scalar_one_or_none()
        if entry:
            return MistakeBookService._format_entry_item(entry)

        return None
