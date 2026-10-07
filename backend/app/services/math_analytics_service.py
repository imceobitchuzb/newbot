from typing import Dict, List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.math_taxonomy import (
    CANONICAL_MATH_DOMAINS,
    calculate_mastery_level,
    normalize_skill,
)
from backend.app.models.enums import MathDomain, QuestionStatus, Subject
from backend.app.models.profile import UserProfile
from backend.app.models.question import Question, QuestionAttempt
from backend.app.schemas.math_practice import (
    DomainAnalyticsOut,
    MathAnalyticsResponse,
    SkillAnalyticsOut,
)


class MathAnalyticsService:
    @staticmethod
    async def get_user_math_analytics(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> MathAnalyticsResponse:
        """
        Computes real math performance analytics for a user across all 4 canonical
        domains and skills based on actual QuestionAttempt history.
        No mock or fake data.
        """
        # 1. Fetch user profile for diagnostic baseline
        profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_res = await db.execute(profile_stmt)
        profile = profile_res.scalar_one_or_none()

        estimated_score_range = None
        if profile and profile.estimated_math_min and profile.estimated_math_max:
            estimated_score_range = f"{profile.estimated_math_min}–{profile.estimated_math_max}"

        # 2. Fetch all attempts by this user for published Math questions
        stmt = (
            select(
                Question.domain,
                Question.skill,
                QuestionAttempt.is_correct,
            )
            .join(Question, QuestionAttempt.question_id == Question.id)
            .where(
                QuestionAttempt.user_id == user_id,
                Question.subject == Subject.MATH.value,
                Question.status == QuestionStatus.PUBLISHED.value,
            )
        )
        res = await db.execute(stmt)
        attempts_rows = res.all()

        # Aggregate data by domain and normalized skill
        domain_stats: Dict[str, Dict] = {}
        skill_stats: Dict[str, Dict[str, Dict]] = {}

        for domain_key in CANONICAL_MATH_DOMAINS:
            domain_stats[domain_key] = {"total": 0, "correct": 0}
            skill_stats[domain_key] = {
                skill: {"total": 0, "correct": 0}
                for skill in CANONICAL_MATH_DOMAINS[domain_key]["skills"]
            }

        total_attempts = 0
        total_correct = 0

        for dom, raw_skill, is_correct in attempts_rows:
            if dom not in domain_stats:
                continue

            total_attempts += 1
            domain_stats[dom]["total"] += 1
            if is_correct:
                total_correct += 1
                domain_stats[dom]["correct"] += 1

            norm_skill = normalize_skill(raw_skill)
            if norm_skill in skill_stats[dom]:
                skill_stats[dom][norm_skill]["total"] += 1
                if is_correct:
                    skill_stats[dom][norm_skill]["correct"] += 1
            else:
                # Skill might be closely mapped or dynamically present
                if norm_skill not in skill_stats[dom]:
                    skill_stats[dom][norm_skill] = {"total": 0, "correct": 0}
                skill_stats[dom][norm_skill]["total"] += 1
                if is_correct:
                    skill_stats[dom][norm_skill]["correct"] += 1

        overall_accuracy = (
            round((total_correct / float(total_attempts)) * 100, 1)
            if total_attempts > 0
            else 0.0
        )

        domains_out: List[DomainAnalyticsOut] = []
        lowest_accuracy_skill: Optional[str] = None
        lowest_skill_acc: float = 101.0
        lowest_accuracy_domain: Optional[str] = None
        lowest_domain_acc: float = 101.0

        for domain_key, info in CANONICAL_MATH_DOMAINS.items():
            d_total = domain_stats[domain_key]["total"]
            d_corr = domain_stats[domain_key]["correct"]
            d_acc = round((d_corr / float(d_total)) * 100, 1) if d_total > 0 else 0.0
            d_mastery = calculate_mastery_level(d_total, d_acc / 100.0).value

            skills_out: List[SkillAnalyticsOut] = []
            for s_name in info["skills"]:
                s_data = skill_stats[domain_key].get(s_name, {"total": 0, "correct": 0})
                s_tot = s_data["total"]
                s_cor = s_data["correct"]
                s_acc = round((s_cor / float(s_tot)) * 100, 1) if s_tot > 0 else 0.0
                s_mast = calculate_mastery_level(s_tot, s_acc / 100.0).value

                skills_out.append(
                    SkillAnalyticsOut(
                        skill=s_name,
                        attempts=s_tot,
                        correct=s_cor,
                        accuracy=s_acc,
                        mastery_level=s_mast,
                    )
                )

                # Prioritize skills with low accuracy that have been attempted
                if s_tot > 0 and s_acc < lowest_skill_acc:
                    lowest_skill_acc = s_acc
                    lowest_accuracy_skill = s_name

            if d_total > 0 and d_acc < lowest_domain_acc:
                lowest_domain_acc = d_acc
                lowest_accuracy_domain = domain_key

            domains_out.append(
                DomainAnalyticsOut(
                    domain=domain_key,
                    title=info["title"],
                    description=info["description"],
                    total_attempts=d_total,
                    correct_attempts=d_corr,
                    accuracy=d_acc,
                    mastery_level=d_mastery,
                    skills=skills_out,
                )
            )

        # Recommendation fallback if no attempts made yet
        if not lowest_accuracy_skill:
            lowest_accuracy_skill = "Linear equations in one variable"
            lowest_accuracy_domain = MathDomain.ALGEBRA.value
        elif not lowest_accuracy_domain:
            lowest_accuracy_domain = MathDomain.ALGEBRA.value

        return MathAnalyticsResponse(
            total_attempts=total_attempts,
            correct_attempts=total_correct,
            overall_accuracy=overall_accuracy,
            estimated_score_range=estimated_score_range,
            domains=domains_out,
            recommended_focus_skill=lowest_accuracy_skill,
            recommended_focus_domain=lowest_accuracy_domain,
        )

    @staticmethod
    async def get_domain_analytics(
        db: AsyncSession,
        user_id: uuid.UUID,
        domain_name: str,
    ) -> Optional[DomainAnalyticsOut]:
        """Fetch analytics specifically for one domain."""
        dom_key = domain_name.upper()
        if dom_key not in CANONICAL_MATH_DOMAINS:
            return None

        all_analytics = await MathAnalyticsService.get_user_math_analytics(db, user_id)
        for d in all_analytics.domains:
            if d.domain == dom_key:
                return d
        return None
