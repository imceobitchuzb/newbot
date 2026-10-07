from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.enums import QuestionStatus
from backend.app.models.question import (
    Passage,
    Question,
    QuestionAttempt,
    QuestionOption,
)


class QuestionRepository:
    async def get_by_id(
        self,
        db: AsyncSession,
        question_id: uuid.UUID,
    ) -> Optional[Question]:
        query = (
            select(Question)
            .where(Question.id == question_id)
            .options(
                selectinload(Question.options),
                selectinload(Question.passage),
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_published(
        self,
        db: AsyncSession,
        subject: Optional[str] = None,
        domain: Optional[str] = None,
        skill: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 20,
    ) -> List[Question]:
        query = (
            select(Question)
            .where(Question.status == QuestionStatus.PUBLISHED.value)
            .options(
                selectinload(Question.options),
                selectinload(Question.passage),
            )
            .order_by(Question.created_at.desc())
        )

        if subject:
            query = query.where(Question.subject == subject.upper())
        if domain:
            query = query.where(Question.domain == domain.upper())
        if skill:
            query = query.where(Question.skill == skill)
        if difficulty:
            query = query.where(Question.difficulty == difficulty.upper())

        query = query.limit(min(limit, 50))
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_random_published(
        self,
        db: AsyncSession,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> Optional[Question]:
        query = (
            select(Question)
            .where(Question.status == QuestionStatus.PUBLISHED.value)
            .options(
                selectinload(Question.options),
                selectinload(Question.passage),
            )
            .order_by(func.random())
            .limit(1)
        )

        if subject:
            query = query.where(Question.subject == subject.upper())
        if difficulty:
            query = query.where(Question.difficulty == difficulty.upper())

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_option_by_id(
        self,
        db: AsyncSession,
        option_id: uuid.UUID,
    ) -> Optional[QuestionOption]:
        query = select(QuestionOption).where(QuestionOption.id == option_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        question: Question,
    ) -> Question:
        db.add(question)
        await db.commit()
        await db.refresh(question)
        return question

    async def create_attempt(
        self,
        db: AsyncSession,
        attempt: QuestionAttempt,
    ) -> QuestionAttempt:
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
        return attempt


question_repository = QuestionRepository()
