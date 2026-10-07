from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.logging import logger
from backend.app.models.profile import UserProfile
from backend.app.models.user import User
from backend.app.repositories.user_repository import user_repository
from backend.app.services.telegram_auth import TelegramUserData


class UserService:
    async def get_or_create_from_telegram(
        self,
        db: AsyncSession,
        tg_user: TelegramUserData,
    ) -> User:
        """
        Retrieves existing user by telegram_id or creates a new user with default learning profile.
        Updates user metadata and activity timestamp upon returning.
        """
        user = await user_repository.get_by_telegram_id(db, tg_user.id)

        now = datetime.now(timezone.utc)

        if not user:
            logger.info(f"Creating new user from Telegram id: {tg_user.id} ({tg_user.first_name})")
            user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                language_code=tg_user.language_code or "en",
                avatar_url=tg_user.photo_url,
                target_score=1400,
                current_score_estimate=700,
                math_estimate=360,
                rw_estimate=340,
                last_active_at=now,
            )
            # Create associated UserProfile
            profile = UserProfile(
                target_score=1400,
                diagnostic_status="not_started",
                study_goal="Score 1400+ in 4 months",
                daily_goal_minutes=30,
            )
            user.profile = profile

            user = await user_repository.create(db, user)
        else:
            # Update user profile metadata from latest Telegram state
            updated = False
            if user.first_name != tg_user.first_name:
                user.first_name = tg_user.first_name
                updated = True
            if user.last_name != tg_user.last_name:
                user.last_name = tg_user.last_name
                updated = True
            if user.username != tg_user.username:
                user.username = tg_user.username
                updated = True
            if tg_user.photo_url and user.avatar_url != tg_user.photo_url:
                user.avatar_url = tg_user.photo_url
                updated = True

            user.last_active_at = now

            # Ensure profile exists if user was created before profile table
            if not user.profile:
                profile = UserProfile(
                    user_id=user.id,
                    target_score=user.target_score or 1400,
                    diagnostic_status="not_started",
                )
                db.add(profile)
                updated = True

            user = await user_repository.update(db, user)

        return user

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Optional[User]:
        return await user_repository.get_by_id(db, user_id)


user_service = UserService()
