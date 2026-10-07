"""Rate limiter for AI Tutor messages."""
import time
from collections import defaultdict
from typing import Dict, List, Optional
from uuid import UUID
from fastapi import HTTPException, status

from backend.app.core.config import settings


class TutorRateLimiter:
    """Sliding-window in-memory rate limiter per user."""

    def __init__(self):
        self._user_timestamps: Dict[UUID, List[float]] = defaultdict(list)

    def check_and_record(self, user_id: UUID) -> None:
        """Check rate limits and record message timestamp. Raise HTTP 429 if exceeded."""
        now = time.time()
        timestamps = self._user_timestamps[user_id]

        # Prune records older than 1 hour (3600 seconds)
        cutoff_hour = now - 3600.0
        self._user_timestamps[user_id] = [t for t in timestamps if t > cutoff_hour]
        timestamps = self._user_timestamps[user_id]

        # Check minute rate limit
        cutoff_minute = now - 60.0
        minute_count = sum(1 for t in timestamps if t > cutoff_minute)
        if minute_count >= settings.TUTOR_MAX_MESSAGES_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: max {settings.TUTOR_MAX_MESSAGES_PER_MINUTE} messages per minute.",
            )

        # Check hourly rate limit
        if len(timestamps) >= settings.TUTOR_MAX_MESSAGES_PER_HOUR:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: max {settings.TUTOR_MAX_MESSAGES_PER_HOUR} messages per hour.",
            )

        # Record this timestamp
        self._user_timestamps[user_id].append(now)

    def reset(self, user_id: Optional[UUID] = None) -> None:
        """Reset rate limiter state for testing."""
        if user_id:
            self._user_timestamps.pop(user_id, None)
        else:
            self._user_timestamps.clear()


tutor_rate_limiter = TutorRateLimiter()
