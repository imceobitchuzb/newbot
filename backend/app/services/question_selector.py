"""Question Engine 2.0 — Centralized Adaptive & Anti-Repetition Question Selector.

Provides scalable, user-aware, randomized, and anti-repetition question selection
supporting 1,000+ to 10,000+ SAT questions with graceful degradation.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import random
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.logging import logger
from backend.app.core.math_taxonomy import normalize_skill
from backend.app.models.enums import Difficulty, QuestionStatus, Subject
from backend.app.models.question import Question, QuestionAttempt


@dataclass
class QuestionSelectionCriteria:
    subject: Optional[str] = None
    domain: Optional[str] = None
    skill: Optional[str] = None
    subskill: Optional[str] = None
    difficulty: Optional[str] = None  # EASY, MEDIUM, HARD, or MIXED
    desmos_allowed: Optional[bool] = None
    desmos_recommended: Optional[bool] = None
    question_type: Optional[str] = None
    count: int = 1
    excluded_question_ids: Set[uuid.UUID] = field(default_factory=set)
    avoid_recently_seen: bool = True
    cooldown_window: int = 30
    prefer_unseen: bool = True
    prefer_weak_skills: bool = True
    seed: Optional[int] = None
    force_question_id: Optional[uuid.UUID] = None


@dataclass
class UserHistorySnapshot:
    seen_ids: Set[uuid.UUID] = field(default_factory=set)
    recent_cooldown_ids: List[uuid.UUID] = field(default_factory=list)
    attempt_counts: Dict[uuid.UUID, int] = field(default_factory=dict)
    correct_question_ids: Set[uuid.UUID] = field(default_factory=set)
    weak_skills: Set[str] = field(default_factory=set)
    mastered_skills: Set[str] = field(default_factory=set)


def _is_adjacent_difficulty(diff1: str, diff2: str) -> bool:
    order = {Difficulty.EASY.value: 1, Difficulty.MEDIUM.value: 2, Difficulty.HARD.value: 3}
    v1 = order.get(diff1.upper(), 0)
    v2 = order.get(diff2.upper(), 0)
    return abs(v1 - v2) == 1


class QuestionSelectorService:
    """Production Question Engine 2.0 selector service."""

    @classmethod
    async def get_user_history_snapshot(
        cls,
        db: AsyncSession,
        user_id: Optional[uuid.UUID],
        cooldown_limit: int = 30,
    ) -> UserHistorySnapshot:
        """Collect comprehensive question attempt history and skill telemetry for user."""
        if not user_id:
            return UserHistorySnapshot()

        # 1. Total attempts and correctness per question
        stmt_attempts = (
            select(
                QuestionAttempt.question_id,
                func.count(QuestionAttempt.id).label("cnt"),
                func.sum(case((QuestionAttempt.is_correct == True, 1), else_=0)).label("correct_cnt"),
            )
            .where(QuestionAttempt.user_id == user_id)
            .group_by(QuestionAttempt.question_id)
        )
        res_attempts = await db.execute(stmt_attempts)
        seen_ids: Set[uuid.UUID] = set()
        attempt_counts: Dict[uuid.UUID, int] = {}
        correct_ids: Set[uuid.UUID] = set()

        for row in res_attempts.all():
            qid = row.question_id
            cnt = row.cnt
            c_cnt = row.correct_cnt or 0
            seen_ids.add(qid)
            attempt_counts[qid] = cnt
            if c_cnt > 0:
                correct_ids.add(qid)

        # 2. Recent cooldown window
        stmt_recent = (
            select(QuestionAttempt.question_id)
            .where(QuestionAttempt.user_id == user_id)
            .order_by(QuestionAttempt.answered_at.desc())
            .limit(cooldown_limit)
        )
        res_recent = await db.execute(stmt_recent)
        recent_cooldown_ids = list(res_recent.scalars().all())

        # 3. Weak & Mastered skills telemetry
        stmt_skills = (
            select(
                Question.skill,
                func.count(QuestionAttempt.id).label("total_cnt"),
                func.sum(case((QuestionAttempt.is_correct == True, 1), else_=0)).label("correct_cnt"),
            )
            .join(Question, QuestionAttempt.question_id == Question.id)
            .where(QuestionAttempt.user_id == user_id)
            .group_by(Question.skill)
        )
        res_skills = await db.execute(stmt_skills)
        weak_skills: Set[str] = set()
        mastered_skills: Set[str] = set()

        for row in res_skills.all():
            skill_name = row.skill
            tot = row.total_cnt
            cor = row.correct_cnt or 0
            acc = cor / tot if tot > 0 else 0.0
            if tot >= 2 and acc < 0.60:
                weak_skills.add(skill_name)
            elif tot >= 3 and acc >= 0.85:
                mastered_skills.add(skill_name)

        return UserHistorySnapshot(
            seen_ids=seen_ids,
            recent_cooldown_ids=recent_cooldown_ids,
            attempt_counts=attempt_counts,
            correct_question_ids=correct_ids,
            weak_skills=weak_skills,
            mastered_skills=mastered_skills,
        )

    @classmethod
    async def select_questions(
        cls,
        db: AsyncSession,
        criteria: QuestionSelectionCriteria,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[Question]:
        """
        Main Question Engine 2.0 entrypoint:
        Selects balanced, randomized, anti-repetition questions matching criteria.
        """
        rng = random.Random(criteria.seed) if criteria.seed is not None else random.Random()

        # If a question is forced (e.g. specific mistake review)
        if criteria.force_question_id:
            forced = await db.get(
                Question,
                criteria.force_question_id,
                options=[selectinload(Question.options), selectinload(Question.passage)],
            )
            if forced and forced.status == QuestionStatus.PUBLISHED.value:
                return [forced]

        # 1. Fetch user history snapshot
        history = await cls.get_user_history_snapshot(
            db=db,
            user_id=user_id,
            cooldown_limit=criteria.cooldown_window,
        )

        # 2. Query published candidates from question pool
        stmt = (
            select(Question)
            .where(Question.status == QuestionStatus.PUBLISHED.value)
            .options(
                selectinload(Question.options),
                selectinload(Question.passage),
            )
        )

        # Hard filters
        if criteria.subject:
            stmt = stmt.where(Question.subject == criteria.subject.upper())

        if criteria.desmos_allowed is not None:
            stmt = stmt.where(Question.desmos_allowed == criteria.desmos_allowed)

        if criteria.desmos_recommended is not None:
            stmt = stmt.where(Question.desmos_recommended == criteria.desmos_recommended)

        if criteria.question_type:
            stmt = stmt.where(Question.question_type == criteria.question_type.upper())

        res = await db.execute(stmt)
        candidates = list(res.scalars().all())

        if not candidates:
            logger.warning(f"Question pool empty for subject {criteria.subject}")
            return []

        # Filter out hard exclusions
        if criteria.excluded_question_ids:
            candidates = [q for q in candidates if q.id not in criteria.excluded_question_ids]

        if not candidates:
            return []

        # 3. Clean filters
        clean_skill = normalize_skill(criteria.skill) if criteria.skill else None
        clean_domain = criteria.domain.upper() if criteria.domain and criteria.domain != "ALL" else None
        clean_diff = criteria.difficulty.upper() if criteria.difficulty and criteria.difficulty != "MIXED" else None

        # 4. Adaptive Weighting Calculation
        scored_candidates: List[Tuple[float, Question]] = []

        for q in candidates:
            score = 100.0

            # Difficulty match
            if clean_diff:
                if q.difficulty == clean_diff:
                    score += 60.0
                elif _is_adjacent_difficulty(q.difficulty, clean_diff):
                    score += 15.0
                else:
                    score -= 30.0

            # Skill match
            if clean_skill:
                if q.skill == clean_skill:
                    score += 90.0
                else:
                    score -= 40.0
            elif clean_domain:
                if q.domain == clean_domain:
                    score += 45.0
                else:
                    score -= 25.0

            # Weak skills priority
            if criteria.prefer_weak_skills and q.skill in history.weak_skills:
                score += 35.0
            elif q.skill in history.mastered_skills:
                score -= 20.0

            # Anti-repetition & Unseen priority
            if q.id not in history.seen_ids:
                if criteria.prefer_unseen:
                    score += 140.0  # Dominant preference for fresh questions
            else:
                att_count = history.attempt_counts.get(q.id, 0)
                score -= min(120.0, att_count * 35.0)

                if criteria.avoid_recently_seen and q.id in history.recent_cooldown_ids:
                    recency_idx = history.recent_cooldown_ids.index(q.id)
                    if recency_idx < 10:
                        score -= 350.0  # Extreme barrier against immediate repetitions
                    else:
                        score -= 180.0

                # Remediation bonus: prioritize questions previously answered incorrectly
                if q.id not in history.correct_question_ids:
                    score += 25.0

            # Stochastic perturbation for natural variety across queries
            noise = rng.uniform(-6.0, 6.0)
            scored_candidates.append((score + noise, q))

        # 5. Sort descending by computed score
        scored_candidates.sort(key=lambda item: item[0], reverse=True)

        # 6. Select top `count` questions
        chosen = [item[1] for item in scored_candidates[: criteria.count]]

        return chosen

    @classmethod
    async def select_single_question(
        cls,
        db: AsyncSession,
        criteria: QuestionSelectionCriteria,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[Question]:
        """Convenience method for selecting 1 question."""
        criteria.count = 1
        results = await cls.select_questions(db, criteria, user_id=user_id)
        return results[0] if results else None
