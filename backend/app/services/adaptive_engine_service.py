from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.core.math_taxonomy import CANONICAL_MATH_DOMAINS, get_all_canonical_skills
from backend.app.models.adaptive import AdaptiveProfile
from backend.app.models.diagnostic import DiagnosticResult, DiagnosticSession
from backend.app.models.enums import (
    AdaptiveSkillStatus,
    Difficulty,
    DomainClassification,
    MathDomain,
    MistakeStatus,
    RecommendationType,
    Subject,
)
from backend.app.models.mistake_book import MistakeBookEntry
from backend.app.models.question import Question, QuestionAttempt
from backend.app.schemas.adaptive import SkillMasteryItem


class AdaptiveEngineService:
    """
    Deterministic, explainable recommendation and mastery computation engine
    for SAT Master.
    """

    @staticmethod
    def calculate_confidence(attempts: int) -> float:
        """
        Confidence formula:
        confidence = min(attempts / 10.0, 1.0)
        """
        if attempts <= 0:
            return 0.0
        return round(min(attempts / 10.0, 1.0), 4)

    @staticmethod
    def calculate_recent_accuracy(attempts_outcomes: List[bool]) -> float:
        """
        Rolling accuracy over the last up to 10 attempts on a skill.
        Outcomes should be ordered newest first.
        """
        if not attempts_outcomes:
            return 0.0
        recent = attempts_outcomes[:10]
        return round(sum(1 for x in recent if x) / float(len(recent)), 4)

    @staticmethod
    def calculate_mastery_score(
        overall_accuracy: float,
        recent_accuracy: float,
        confidence: float,
        has_active_mistake: bool = False,
        has_in_review_mistake: bool = False,
    ) -> float:
        """
        Deterministic mastery score:
        base_accuracy = 0.4 * overall_accuracy + 0.6 * recent_accuracy
        mistake_factor = 0.85 if active mistake else (0.95 if in_review else 1.0)
        mastery = confidence * (base_accuracy * mistake_factor)
        """
        if confidence <= 0.0:
            return 0.0
        base_acc = 0.4 * overall_accuracy + 0.6 * recent_accuracy
        factor = 1.0
        if has_active_mistake:
            factor = 0.85
        elif has_in_review_mistake:
            factor = 0.95
        raw_mastery = base_acc * factor
        return round(max(0.0, min(1.0, confidence * raw_mastery)), 4)

    @staticmethod
    def determine_skill_status(
        attempts: int,
        mastery_score: float,
        recent_accuracy: float,
    ) -> str:
        """
        Strict threshold definitions:
        NOT_STARTED: attempts == 0
        LEARNING: mastery < 0.60
        PRACTICING: 0.60 <= mastery < 0.80
        STRONG: 0.80 <= mastery < 0.90
        MASTERED: mastery >= 0.90 AND attempts >= 10 AND recent_accuracy >= 0.85
        """
        if attempts == 0:
            return AdaptiveSkillStatus.NOT_STARTED.value
        if mastery_score < 0.60:
            return AdaptiveSkillStatus.LEARNING.value
        if mastery_score < 0.80:
            return AdaptiveSkillStatus.PRACTICING.value
        if mastery_score >= 0.90 and attempts >= 10 and recent_accuracy >= 0.85:
            return AdaptiveSkillStatus.MASTERED.value
        return AdaptiveSkillStatus.STRONG.value

    @staticmethod
    def calculate_next_difficulty(
        current_difficulty: str,
        recent_results: List[bool],
    ) -> str:
        """
        Difficulty transition based on a rolling window of recent questions:
        >= 80% correct (e.g. 4/5) -> step up
        <= 40% correct (e.g. <= 2/5) -> step down
        Otherwise -> maintain
        Transitions are strictly single-step (EASY <-> MEDIUM <-> HARD).
        """
        if len(recent_results) < 3:
            return current_difficulty

        # Use up to 5 most recent results
        window = recent_results[:5]
        acc = sum(1 for x in window if x) / float(len(window))

        if acc >= 0.80:
            if current_difficulty == Difficulty.EASY.value:
                return Difficulty.MEDIUM.value
            if current_difficulty == Difficulty.MEDIUM.value:
                return Difficulty.HARD.value
            return Difficulty.HARD.value
        elif acc <= 0.40:
            if current_difficulty == Difficulty.HARD.value:
                return Difficulty.MEDIUM.value
            if current_difficulty == Difficulty.MEDIUM.value:
                return Difficulty.EASY.value
            return Difficulty.EASY.value
        return current_difficulty

    @classmethod
    async def get_user_skill_analytics(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        subject: str = Subject.MATH.value,
    ) -> Dict[str, SkillMasteryItem]:
        """
        Computes deterministic skill telemetry for all canonical skills in the subject.
        """
        # 1. Fetch all user attempts on questions belonging to the subject
        attempts_stmt = (
            select(
                Question.skill,
                Question.domain,
                Question.difficulty,
                QuestionAttempt.is_correct,
                QuestionAttempt.answered_at,
            )
            .join(Question, QuestionAttempt.question_id == Question.id)
            .where(
                QuestionAttempt.user_id == user_id,
                Question.subject == subject,
            )
            .order_by(QuestionAttempt.answered_at.desc())
        )
        res = await db.execute(attempts_stmt)
        rows = res.all()

        # Group attempts by skill
        skill_attempts: Dict[str, List[Tuple[str, str, bool, datetime]]] = {}
        for r in rows:
            skill = r[0]
            if skill not in skill_attempts:
                skill_attempts[skill] = []
            skill_attempts[skill].append((r[1], r[2], r[3], r[4]))

        # 2. Fetch active mistake entries for user
        mistakes_stmt = (
            select(MistakeBookEntry.skill, MistakeBookEntry.status)
            .where(
                MistakeBookEntry.user_id == user_id,
                MistakeBookEntry.subject == subject,
            )
        )
        mistakes_res = await db.execute(mistakes_stmt)
        mistake_rows = mistakes_res.all()

        active_mistakes_by_skill: Set[str] = set()
        in_review_mistakes_by_skill: Set[str] = set()
        for m_skill, m_status in mistake_rows:
            if m_status == MistakeStatus.ACTIVE.value:
                active_mistakes_by_skill.add(m_skill)
            elif m_status == MistakeStatus.IN_REVIEW.value:
                in_review_mistakes_by_skill.add(m_skill)

        # 3. Build analytics map covering all canonical skills
        canonical_skills = get_all_canonical_skills()
        skill_map: Dict[str, SkillMasteryItem] = {}

        # Determine domain for each canonical skill
        skill_to_domain: Dict[str, str] = {}
        for d_key, d_data in CANONICAL_MATH_DOMAINS.items():
            for s in d_data["skills"]:
                skill_to_domain[s] = d_key

        for skill in canonical_skills:
            domain = skill_to_domain.get(skill, MathDomain.ALGEBRA.value)
            raw_data = skill_attempts.get(skill, [])

            total_attempts = len(raw_data)
            has_active = skill in active_mistakes_by_skill
            has_in_review = skill in in_review_mistakes_by_skill

            if total_attempts == 0:
                skill_map[skill] = SkillMasteryItem(
                    skill=skill,
                    domain=domain,
                    status=AdaptiveSkillStatus.NOT_STARTED.value,
                    mastery_score=0.0,
                    confidence_score=0.0,
                    attempts=0,
                    accuracy=0.0,
                    recent_accuracy=0.0,
                    easy_accuracy=0.0,
                    medium_accuracy=0.0,
                    hard_accuracy=0.0,
                    has_active_mistake=has_active,
                )
                continue

            correct_count = sum(1 for item in raw_data if item[2])
            overall_acc = round(correct_count / float(total_attempts), 4)

            # raw_data is already ordered newest first
            outcomes = [item[2] for item in raw_data]
            recent_acc = cls.calculate_recent_accuracy(outcomes)
            confidence = cls.calculate_confidence(total_attempts)
            mastery = cls.calculate_mastery_score(
                overall_accuracy=overall_acc,
                recent_accuracy=recent_acc,
                confidence=confidence,
                has_active_mistake=has_active,
                has_in_review_mistake=has_in_review,
            )

            status = cls.determine_skill_status(total_attempts, mastery, recent_acc)

            # Difficulty breakdown
            easy_items = [item for item in raw_data if item[1] == Difficulty.EASY.value]
            med_items = [item for item in raw_data if item[1] == Difficulty.MEDIUM.value]
            hard_items = [item for item in raw_data if item[1] == Difficulty.HARD.value]

            easy_acc = (
                round(sum(1 for x in easy_items if x[2]) / float(len(easy_items)), 4)
                if easy_items
                else 0.0
            )
            med_acc = (
                round(sum(1 for x in med_items if x[2]) / float(len(med_items)), 4)
                if med_items
                else 0.0
            )
            hard_acc = (
                round(sum(1 for x in hard_items if x[2]) / float(len(hard_items)), 4)
                if hard_items
                else 0.0
            )

            skill_map[skill] = SkillMasteryItem(
                skill=skill,
                domain=domain,
                status=status,
                mastery_score=mastery,
                confidence_score=confidence,
                attempts=total_attempts,
                accuracy=overall_acc,
                recent_accuracy=recent_acc,
                easy_accuracy=easy_acc,
                medium_accuracy=med_acc,
                hard_accuracy=hard_acc,
                has_active_mistake=has_active,
            )

        return skill_map

    @classmethod
    async def get_diagnostic_weak_domains(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Set[str]:
        """
        Inspects user's completed diagnostic result to identify baseline weak domains (< 60%).
        """
        stmt = (
            select(DiagnosticResult)
            .join(DiagnosticSession, DiagnosticResult.session_id == DiagnosticSession.id)
            .where(DiagnosticSession.user_id == user_id)
            .order_by(DiagnosticResult.completed_at.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        result = res.scalar_one_or_none()
        if not result or not result.domain_breakdown:
            return set()

        weak = set()
        for dom, stats in result.domain_breakdown.items():
            if stats.get("classification") == DomainClassification.WEAK.value:
                weak.add(dom)
            elif stats.get("total", 0) > 0 and (stats.get("correct", 0) / float(stats["total"])) < 0.60:
                weak.add(dom)
        return weak

    @classmethod
    async def determine_next_recommendation(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        subject: str = Subject.MATH.value,
        current_difficulty: str = Difficulty.MEDIUM.value,
    ) -> Tuple[str, str, str, str, str, Optional[uuid.UUID]]:
        """
        Deterministic recommendation engine.
        Returns:
        (recommendation_type, target_domain, target_skill, target_difficulty, reason, mistake_question_id)
        """
        now = datetime.now(timezone.utc)

        # 1. Check for OVERDUE mistake in Mistake Book
        overdue_stmt = (
            select(MistakeBookEntry)
            .where(
                MistakeBookEntry.user_id == user_id,
                MistakeBookEntry.subject == subject,
                MistakeBookEntry.status.in_([MistakeStatus.ACTIVE.value, MistakeStatus.IN_REVIEW.value]),
                MistakeBookEntry.next_review_at <= now,
            )
            .order_by(
                MistakeBookEntry.next_review_at.asc(),
                MistakeBookEntry.incorrect_retry_count.desc(),
                MistakeBookEntry.id.asc(),
            )
            .limit(1)
        )
        overdue_res = await db.execute(overdue_stmt)
        overdue_entry = overdue_res.scalar_one_or_none()

        if overdue_entry:
            return (
                RecommendationType.MISTAKE_REVIEW.value,
                overdue_entry.domain,
                overdue_entry.skill,
                current_difficulty,
                f"You have an overdue review for a missed question in {overdue_entry.skill}.",
                overdue_entry.question_id,
            )

        # 2. Compute skill analytics
        skill_analytics = await cls.get_user_skill_analytics(db, user_id, subject)
        diagnostic_weak_domains = await cls.get_diagnostic_weak_domains(db, user_id)

        # 3. Check for ACTIVE mistakes that are not overdue yet
        active_mistake_stmt = (
            select(MistakeBookEntry)
            .where(
                MistakeBookEntry.user_id == user_id,
                MistakeBookEntry.subject == subject,
                MistakeBookEntry.status == MistakeStatus.ACTIVE.value,
            )
            .order_by(
                MistakeBookEntry.incorrect_retry_count.desc(),
                MistakeBookEntry.created_at.asc(),
                MistakeBookEntry.id.asc(),
            )
            .limit(1)
        )
        act_res = await db.execute(active_mistake_stmt)
        active_entry = act_res.scalar_one_or_none()

        # If user has an active mistake with 2+ failed retries, prioritize it!
        if active_entry and active_entry.incorrect_retry_count >= 2:
            return (
                RecommendationType.MISTAKE_REVIEW.value,
                active_entry.domain,
                active_entry.skill,
                current_difficulty,
                f"Active conceptual error in {active_entry.skill}. Deliberate retry recommended.",
                active_entry.question_id,
            )

        # 4. Deterministic score calculation across skills
        candidates = []
        for skill_name, item in skill_analytics.items():
            base_priority = 0.0
            rec_type = RecommendationType.WEAK_SKILL.value
            rec_reason = ""
            target_diff = current_difficulty

            # Diagnostic weak domain bonus
            diag_bonus = 25.0 if (item.domain in diagnostic_weak_domains and item.attempts < 5) else 0.0

            if item.has_active_mistake:
                base_priority = 400.0 + (1.0 - item.mastery_score) * 50.0 + diag_bonus
                rec_type = RecommendationType.MISTAKE_REVIEW.value
                rec_reason = f"Active error tracked in {skill_name}. Reinforce core method."
            elif item.status == AdaptiveSkillStatus.LEARNING.value:
                # Weak skill with attempts
                base_priority = 200.0 + (1.0 - item.mastery_score) * 100.0 + diag_bonus
                rec_type = RecommendationType.WEAK_SKILL.value
                pct = int(item.accuracy * 100)
                rec_reason = f"Your accuracy in {skill_name} is {pct}%. Targeted drill will build mastery."
            elif item.status == AdaptiveSkillStatus.NOT_STARTED.value:
                base_priority = 100.0 + diag_bonus
                rec_type = RecommendationType.NEW_SKILL.value
                rec_reason = f"Expand syllabus coverage: you have not practiced {skill_name} yet."
            elif item.status == AdaptiveSkillStatus.PRACTICING.value:
                # Check for step up or step down
                if item.recent_accuracy >= 0.80 and current_difficulty == Difficulty.MEDIUM.value:
                    base_priority = 80.0 + (1.0 - item.mastery_score) * 20.0
                    rec_type = RecommendationType.DIFFICULTY_UP.value
                    target_diff = Difficulty.HARD.value
                    rec_reason = f"Strong accuracy on {skill_name}. Stepping up to Hard questions."
                elif item.recent_accuracy <= 0.40 and current_difficulty in [Difficulty.HARD.value, Difficulty.MEDIUM.value]:
                    base_priority = 85.0 + (1.0 - item.mastery_score) * 20.0
                    rec_type = RecommendationType.DIFFICULTY_DOWN.value
                    target_diff = Difficulty.EASY.value if current_difficulty == Difficulty.MEDIUM.value else Difficulty.MEDIUM.value
                    rec_reason = f"Recent accuracy dipped in {skill_name}. Stepping down to solidify mechanics."
                else:
                    base_priority = 60.0 + (1.0 - item.mastery_score) * 30.0
                    rec_type = RecommendationType.WEAK_SKILL.value
                    pct = int(item.accuracy * 100)
                    rec_reason = f"Practicing {skill_name} (current accuracy: {pct}%)."
            else:
                # STRONG or MASTERED
                base_priority = 10.0 + (1.0 - item.mastery_score) * 10.0
                rec_type = RecommendationType.MAINTENANCE.value
                pct = int(item.mastery_score * 100)
                rec_reason = f"Maintaining retention in {skill_name} (mastery: {pct}%)."

            # Tie-break deterministically with skill_name
            candidates.append((base_priority, skill_name, item.domain, target_diff, rec_type, rec_reason))

        # Sort descending by priority, then ascending by skill_name
        candidates.sort(key=lambda c: (-c[0], c[1]))
        top = candidates[0]

        return (
            top[4],  # rec_type
            top[2],  # domain
            top[1],  # skill
            top[3],  # difficulty
            top[5],  # reason
            None,    # no specific question ID
        )

    @classmethod
    async def select_question(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        target_domain: str,
        target_skill: str,
        target_difficulty: str,
        excluded_question_ids: Optional[Set[uuid.UUID]] = None,
        subject: str = Subject.MATH.value,
        force_question_id: Optional[uuid.UUID] = None,
    ) -> Optional[Question]:
        """
        Deterministic question selection with hierarchical fallbacks.
        Guaranteed to return a question as long as at least 1 published question exists.
        """
        from backend.app.services.question_selector import (
            QuestionSelectionCriteria,
            QuestionSelectorService,
        )

        criteria = QuestionSelectionCriteria(
            subject=subject,
            domain=target_domain,
            skill=target_skill,
            difficulty=target_difficulty,
            excluded_question_ids=excluded_question_ids or set(),
            avoid_recently_seen=True,
            cooldown_window=20,
            prefer_unseen=True,
            prefer_weak_skills=True,
            force_question_id=force_question_id,
        )
        cand = await QuestionSelectorService.select_single_question(
            db=db,
            criteria=criteria,
            user_id=user_id,
        )
        if cand:
            return cand

        # Fallback to any published question in subject if pool was exhausted
        fallback_stmt = (
            select(Question)
            .where(
                Question.subject == subject,
                Question.status == "PUBLISHED",
            )
            .options(selectinload(Question.options), selectinload(Question.passage))
            .limit(1)
        )
        res = await db.execute(fallback_stmt)
        return res.scalar_one_or_none()
