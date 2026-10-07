from typing import Any, Dict, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.logging import logger
from backend.app.models.diagnostic import DiagnosticResult, DiagnosticSession
from backend.app.models.enums import DomainClassification, Subject
from backend.app.models.profile import UserProfile


class DiagnosticResultService:
    """
    Computes deterministic SAT Master score range estimates and domain strengths/weaknesses.
    Updates UserProfile on completion while strictly preserving the student's target score.
    """

    WEAK_THRESHOLD_PERCENT = 60.0
    STRONG_THRESHOLD_PERCENT = 75.0

    @classmethod
    def calculate_section_estimate(cls, correct: int, total: int = 20) -> Tuple[int, int]:
        """
        Calculates deterministic SAT section score range (200 - 800) based on raw correct count out of total.
        Returns (low, high).
        """
        if total <= 0:
            return 200, 240

        ratio = max(0.0, min(1.0, correct / float(total)))
        # Scaled midpoint on 200 - 800 scale rounded to nearest 10
        midpoint = 200 + int(round((600 * ratio) / 10.0)) * 10

        if correct == 0:
            return 200, 240
        if correct >= total:
            return 760, 800

        low = max(200, midpoint - 30)
        high = min(800, midpoint + 30)
        return low, high

    @classmethod
    def calculate_total_estimate(cls, math_range: Tuple[int, int], rw_range: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calculates total SAT estimate (400 - 1600).
        """
        total_low = math_range[0] + rw_range[0]
        total_high = math_range[1] + rw_range[1]
        return total_low, total_high

    @classmethod
    def classify_domain(cls, accuracy_pct: float) -> str:
        if accuracy_pct < cls.WEAK_THRESHOLD_PERCENT:
            return DomainClassification.WEAK.value
        elif accuracy_pct >= cls.STRONG_THRESHOLD_PERCENT:
            return DomainClassification.STRONG.value
        else:
            return DomainClassification.MODERATE.value

    @classmethod
    async def create_and_store_result(
        cls,
        db: AsyncSession,
        session: DiagnosticSession,
    ) -> DiagnosticResult:
        """
        Evaluates answers across session modules, constructs DiagnosticResult, and updates UserProfile.
        """
        # Check if result already exists
        res_stmt = select(DiagnosticResult).where(DiagnosticResult.session_id == session.id)
        res_exec = await db.execute(res_stmt)
        existing_result = res_exec.scalar_one_or_none()
        if existing_result:
            return existing_result


        math_correct = 0
        math_total = 0
        rw_correct = 0
        rw_total = 0
        total_duration = 0

        # Domain accumulator: domain_name -> {"subject": ..., "total": ..., "correct": ...}
        domains_stats: Dict[str, Dict[str, Any]] = {}

        for module in session.modules:
            for dq in module.questions:
                total_duration += dq.time_spent_seconds or 0
                is_correct = bool(dq.is_correct)
                domain = dq.question.domain
                subj = dq.question.subject

                if domain not in domains_stats:
                    domains_stats[domain] = {
                        "subject": subj,
                        "total": 0,
                        "correct": 0,
                    }
                domains_stats[domain]["total"] += 1
                if is_correct:
                    domains_stats[domain]["correct"] += 1

                if module.subject == Subject.MATH.value:
                    math_total += 1
                    if is_correct:
                        math_correct += 1
                elif module.subject == Subject.READING_WRITING.value:
                    rw_total += 1
                    if is_correct:
                        rw_correct += 1

        math_total = max(1, math_total)
        rw_total = max(1, rw_total)

        math_acc = round(math_correct / float(math_total), 4)
        rw_acc = round(rw_correct / float(rw_total), 4)
        total_acc = round((math_correct + rw_correct) / float(math_total + rw_total), 4)

        math_low, math_high = cls.calculate_section_estimate(math_correct, math_total)
        rw_low, rw_high = cls.calculate_section_estimate(rw_correct, rw_total)
        total_low, total_high = cls.calculate_total_estimate((math_low, math_high), (rw_low, rw_high))

        domain_breakdown: List[Dict[str, Any]] = []
        weak_domains: List[str] = []
        strong_domains: List[str] = []

        for domain, stats in domains_stats.items():
            tot = stats["total"]
            corr = stats["correct"]
            acc_pct = round((corr / float(tot)) * 100.0, 1) if tot > 0 else 0.0
            classification = cls.classify_domain(acc_pct)

            if classification == DomainClassification.WEAK.value:
                weak_domains.append(domain)
            elif classification == DomainClassification.STRONG.value:
                strong_domains.append(domain)

            domain_breakdown.append({
                "domain": domain,
                "subject": stats["subject"],
                "total_questions": tot,
                "correct_questions": corr,
                "accuracy": acc_pct,
                "classification": classification,
            })

        # Sort breakdown by subject then domain name
        domain_breakdown.sort(key=lambda x: (x["subject"], x["domain"]))

        diagnostic_result = DiagnosticResult(
            session_id=session.id,
            math_correct=math_correct,
            math_total=math_total,
            rw_correct=rw_correct,
            rw_total=rw_total,
            math_accuracy=math_acc,
            rw_accuracy=rw_acc,
            total_accuracy=total_acc,
            estimated_math_low=math_low,
            estimated_math_high=math_high,
            estimated_rw_low=rw_low,
            estimated_rw_high=rw_high,
            estimated_total_low=total_low,
            estimated_total_high=total_high,
            duration_seconds=total_duration,
            domain_breakdown=domain_breakdown,
            weak_domains=weak_domains,
            strong_domains=strong_domains,
        )
        db.add(diagnostic_result)

        # Update UserProfile
        profile_stmt = select(UserProfile).where(UserProfile.user_id == session.user_id)
        profile_res = await db.execute(profile_stmt)
        profile = profile_res.scalar_one_or_none()
        if profile:
            profile.diagnostic_status = "completed"
            profile.math_estimate = round((math_low + math_high) / 2.0)
            profile.rw_estimate = round((rw_low + rw_high) / 2.0)
            # Strictly do not overwrite profile.target_score!

        await db.commit()
        await db.refresh(diagnostic_result)
        return diagnostic_result
