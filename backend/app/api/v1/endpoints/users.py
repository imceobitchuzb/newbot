from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.models.profile import UserProfile
from backend.app.models.user import User
from backend.app.schemas.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated student profile and learning state",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the currently authenticated user's profile, including learning goals and diagnostic status.
    Requires Bearer authorization.
    If UserProfile is missing, automatically creates one with safe defaults.
    """
    logger.info(f"[GET /users/me] Fetching profile for user {current_user.id} (tg_id={current_user.telegram_id})")

    if not current_user.profile:
        logger.info(f"[PROFILE CREATED] Auto-creating missing UserProfile for user {current_user.id}")
        profile = UserProfile(
            user_id=current_user.id,
            target_score=current_user.target_score or 1400,
            diagnostic_status="not_started",
            study_goal="Score 1400+ in 4 months",
            daily_goal_minutes=30,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        current_user.profile = profile

    return UserResponse.model_validate(current_user)
