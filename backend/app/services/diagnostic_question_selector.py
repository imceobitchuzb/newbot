from typing import Dict, List, Set, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.core.logging import logger
from backend.app.models.enums import (
    Difficulty,
    MathDomain,
    QuestionStatus,
    ReadingWritingDomain,
    Subject,
)
from backend.app.models.question import Question


class DiagnosticQuestionSelector:
    """
    Selects balanced questions for a 40-question SAT Master Diagnostic test:
    - 20 Math questions (5 from each of the 4 domains, difficulty balanced ~25% Easy, ~50% Med, ~25% Hard)
    - 20 Reading & Writing questions (5 from each of the 4 domains, difficulty balanced ~25% Easy, ~50% Med, ~25% Hard)
    Guarantees no duplicate question IDs across the session.
    """

    # Target per-domain difficulty distribution
    # Domain -> {EASY: count, MEDIUM: count, HARD: count} = 5 questions per domain
    MATH_TARGET_DISTRIBUTION = {
        MathDomain.ALGEBRA.value: {Difficulty.EASY.value: 1, Difficulty.MEDIUM.value: 3, Difficulty.HARD.value: 1},
        MathDomain.ADVANCED_MATH.value: {Difficulty.EASY.value: 1, Difficulty.MEDIUM.value: 2, Difficulty.HARD.value: 2},
        MathDomain.PROBLEM_SOLVING_DATA_ANALYSIS.value: {Difficulty.EASY.value: 2, Difficulty.MEDIUM.value: 2, Difficulty.HARD.value: 1},
        MathDomain.GEOMETRY_TRIGONOMETRY.value: {Difficulty.EASY.value: 1, Difficulty.MEDIUM.value: 3, Difficulty.HARD.value: 1},
    }

    RW_TARGET_DISTRIBUTION = {
        ReadingWritingDomain.INFORMATION_IDEAS.value: {Difficulty.EASY.value: 1, Difficulty.MEDIUM.value: 3, Difficulty.HARD.value: 1},
        ReadingWritingDomain.CRAFT_STRUCTURE.value: {Difficulty.EASY.value: 1, Difficulty.MEDIUM.value: 2, Difficulty.HARD.value: 2},
        ReadingWritingDomain.EXPRESSION_IDEAS.value: {Difficulty.EASY.value: 2, Difficulty.MEDIUM.value: 2, Difficulty.HARD.value: 1},
        ReadingWritingDomain.STANDARD_ENGLISH_CONVENTIONS.value: {Difficulty.EASY.value: 1, Difficulty.MEDIUM.value: 3, Difficulty.HARD.value: 1},
    }

    @classmethod
    async def select_questions(cls, db: AsyncSession) -> Tuple[List[Question], List[Question]]:
        """
        Selects 20 Math and 20 Reading & Writing questions.
        Returns (math_questions, rw_questions).
        Raises ValueError if insufficient questions are published.
        """
        stmt = (
            select(Question)
            .where(Question.status == QuestionStatus.PUBLISHED.value)
            .options(selectinload(Question.options), selectinload(Question.passage))
            .order_by(Question.created_at.asc())
        )
        result = await db.execute(stmt)
        all_published = list(result.scalars().all())

        selected_ids: Set[str] = set()

        math_questions = cls._select_for_subject(
            all_published=all_published,
            subject=Subject.MATH.value,
            domain_targets=cls.MATH_TARGET_DISTRIBUTION,
            selected_ids=selected_ids,
            target_total=20,
        )

        rw_questions = cls._select_for_subject(
            all_published=all_published,
            subject=Subject.READING_WRITING.value,
            domain_targets=cls.RW_TARGET_DISTRIBUTION,
            selected_ids=selected_ids,
            target_total=20,
        )

        if len(math_questions) != 20 or len(rw_questions) != 20:
            raise ValueError(
                f"Question bank has insufficient questions to form diagnostic: "
                f"Math={len(math_questions)}/20, RW={len(rw_questions)}/20. "
                f"At least 20 published Math and 20 published RW questions are required."
            )

        if len(selected_ids) != 40:
            raise ValueError(
                f"Duplicate questions detected in diagnostic selection: "
                f"Unique count={len(selected_ids)}/40."
            )

        return math_questions, rw_questions

    @classmethod
    def _select_for_subject(
        cls,
        all_published: List[Question],
        subject: str,
        domain_targets: Dict[str, Dict[str, int]],
        selected_ids: Set[str],
        target_total: int,
    ) -> List[Question]:
        subject_pool = [q for q in all_published if q.subject == subject and str(q.id) not in selected_ids]
        selected: List[Question] = []

        # Pass 1: Select according to exact domain and difficulty targets
        for domain, diff_targets in domain_targets.items():
            domain_pool = [q for q in subject_pool if q.domain == domain]
            for diff, count in diff_targets.items():
                matching = [
                    q for q in domain_pool
                    if q.difficulty == diff and str(q.id) not in selected_ids
                ]
                for q in matching[:count]:
                    selected.append(q)
                    selected_ids.add(str(q.id))

        # Pass 2: If any domain has fewer than 5, fill from remaining domain pool
        for domain in domain_targets.keys():
            current_domain_count = sum(1 for q in selected if q.domain == domain)
            needed = 5 - current_domain_count
            if needed > 0:
                domain_rem = [
                    q for q in subject_pool
                    if q.domain == domain and str(q.id) not in selected_ids
                ]
                for q in domain_rem[:needed]:
                    selected.append(q)
                    selected_ids.add(str(q.id))

        # Pass 3: If still short of target_total, fill from subject pool
        if len(selected) < target_total:
            remaining = [
                q for q in subject_pool
                if str(q.id) not in selected_ids
            ]
            deficit = target_total - len(selected)
            for q in remaining[:deficit]:
                selected.append(q)
                selected_ids.add(str(q.id))

        return selected[:target_total]
