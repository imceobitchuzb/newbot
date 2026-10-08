from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.logging import logger
from backend.app.models.enums import QuestionStatus
from backend.app.models.question import Question, QuestionAttempt
from backend.app.repositories.question_repository import question_repository
from backend.app.schemas.question import (
    AttemptResultResponse,
    AttemptSubmitRequest,
    QuestionPublic,
)


from backend.app.services.question_selector import (
    QuestionSelectionCriteria,
    QuestionSelectorService,
)


class QuestionService:
    async def list_published(
        self,
        db: AsyncSession,
        subject: Optional[str] = None,
        domain: Optional[str] = None,
        skill: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 20,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[QuestionPublic]:
        criteria = QuestionSelectionCriteria(
            subject=subject,
            domain=domain,
            skill=skill,
            difficulty=difficulty,
            count=min(limit, 50),
            avoid_recently_seen=True if user_id else False,
            prefer_unseen=True if user_id else False,
        )
        questions = await QuestionSelectorService.select_questions(
            db=db,
            criteria=criteria,
            user_id=user_id,
        )
        if not questions:
            # Fallback to direct repo query if selector criteria yielded nothing
            questions = await question_repository.list_published(
                db,
                subject=subject,
                domain=domain,
                skill=skill,
                difficulty=difficulty,
                limit=limit,
            )
        return [QuestionPublic.model_validate(q) for q in questions]

    async def get_for_learner(
        self,
        db: AsyncSession,
        question_id: uuid.UUID,
    ) -> QuestionPublic:
        question = await question_repository.get_by_id(db, question_id)
        if not question or question.status != QuestionStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found or unavailable.",
            )
        return QuestionPublic.model_validate(question)

    async def get_random_for_learner(
        self,
        db: AsyncSession,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> QuestionPublic:
        criteria = QuestionSelectionCriteria(
            subject=subject,
            difficulty=difficulty,
            count=1,
            avoid_recently_seen=True if user_id else False,
            prefer_unseen=True if user_id else False,
        )
        question = await QuestionSelectorService.select_single_question(
            db=db,
            criteria=criteria,
            user_id=user_id,
        )
        if not question:
            # Fallback to random repo query
            question = await question_repository.get_random_published(
                db,
                subject=subject,
                difficulty=difficulty,
            )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions found matching criteria.",
            )
        return QuestionPublic.model_validate(question)

    async def submit_attempt(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        question_id: uuid.UUID,
        payload: AttemptSubmitRequest,
    ) -> AttemptResultResponse:
        question = await question_repository.get_by_id(db, question_id)
        if not question or question.status != QuestionStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found or unavailable for attempts.",
            )

        # Validate that selected option belongs to this question
        chosen_option = next(
            (opt for opt in question.options if opt.id == payload.selected_option_id),
            None,
        )
        if not chosen_option:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected option does not belong to the submitted question.",
            )

        # Identify correct option
        correct_option = next(
            (opt for opt in question.options if opt.is_correct),
            None,
        )
        if not correct_option:
            logger.error(f"Question {question.id} has no marked correct option!")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Corrupted question data: missing correct answer.",
            )

        is_correct = chosen_option.is_correct

        attempt = QuestionAttempt(
            user_id=user_id,
            question_id=question.id,
            selected_option_id=chosen_option.id,
            is_correct=is_correct,
            time_spent_seconds=payload.time_spent_seconds,
        )

        saved_attempt = await question_repository.create_attempt(db, attempt)

        return AttemptResultResponse(
            attempt_id=saved_attempt.id,
            question_id=question.id,
            selected_option_id=chosen_option.id,
            is_correct=is_correct,
            correct_option_id=correct_option.id,
            explanation=question.explanation,
            hint=question.hint,
            sat_shortcut=question.sat_shortcut,
            time_spent_seconds=saved_attempt.time_spent_seconds,
            answered_at=saved_attempt.answered_at,
        )


question_service = QuestionService()
