from datetime import datetime, timezone
from typing import Dict
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.enums import MistakeStatus
from backend.app.models.mistake_book import MistakeBookEntry
from backend.app.schemas.mistake_book import MistakeAnalyticsResponse


def normalize_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class MistakeAnalyticsService:
    @staticmethod
    async def get_user_mistake_analytics(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> MistakeAnalyticsResponse:
        """
        Computes real aggregated mistake book analytics directly from the database.
        No mock or client-side calculation.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch all entries for this user
        stmt = select(MistakeBookEntry).where(MistakeBookEntry.user_id == user_id)
        res = await db.execute(stmt)
        entries = list(res.scalars().all())

        total_mistakes = len(entries)
        active_mistakes = 0
        in_review_mistakes = 0
        mastered_mistakes = 0
        due_reviews = 0
        total_retries = 0

        by_subject: Dict[str, int] = {}
        by_domain: Dict[str, int] = {}
        by_skill: Dict[str, int] = {}
        by_mistake_type: Dict[str, int] = {}

        for e in entries:
            # Status counts
            if e.status == MistakeStatus.ACTIVE.value:
                active_mistakes += 1
            elif e.status == MistakeStatus.IN_REVIEW.value:
                in_review_mistakes += 1
            elif e.status == MistakeStatus.MASTERED.value:
                mastered_mistakes += 1

            # Due review count
            e_next = normalize_to_utc(e.next_review_at)
            if e_next and e_next <= now and e.status not in [MistakeStatus.MASTERED.value, MistakeStatus.DISMISSED.value]:
                due_reviews += 1


            # Retries count
            total_retries += (e.correct_retry_count + e.incorrect_retry_count)

            # Categorical distributions
            by_subject[e.subject] = by_subject.get(e.subject, 0) + 1
            by_domain[e.domain] = by_domain.get(e.domain, 0) + 1
            by_skill[e.skill] = by_skill.get(e.skill, 0) + 1
            by_mistake_type[e.mistake_type] = by_mistake_type.get(e.mistake_type, 0) + 1

        mastery_rate = (
            round((mastered_mistakes / float(total_mistakes)) * 100, 1)
            if total_mistakes > 0
            else 0.0
        )
        average_retries = (
            round(total_retries / float(total_mistakes), 1)
            if total_mistakes > 0
            else 0.0
        )

        return MistakeAnalyticsResponse(
            total_mistakes=total_mistakes,
            active_mistakes=active_mistakes,
            in_review_mistakes=in_review_mistakes,
            mastered_mistakes=mastered_mistakes,
            due_reviews=due_reviews,
            mastery_rate=mastery_rate,
            average_retries=average_retries,
            by_subject=by_subject,
            by_domain=by_domain,
            by_skill=by_skill,
            by_mistake_type=by_mistake_type,
        )
