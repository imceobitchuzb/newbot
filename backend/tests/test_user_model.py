import uuid
import pytest
from sqlalchemy import select
from backend.app.core.database import async_session_factory
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_user_creation_and_retrieval():
    test_tg_id = 9988776655
    async with async_session_factory() as session:
        # Clean up existing test user if present
        existing = await session.execute(select(User).where(User.telegram_id == test_tg_id))
        user_row = existing.scalar_one_or_none()
        if user_row:
            await session.delete(user_row)
            await session.commit()

        # Create user
        new_user = User(
            telegram_id=test_tg_id,
            username="student_sat_top",
            first_name="Diana",
            last_name="Prince",
            target_score=1500,
            current_score_estimate=700,
            math_estimate=360,
            rw_estimate=340,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        assert isinstance(new_user.id, uuid.UUID)
        assert new_user.telegram_id == test_tg_id
        assert new_user.target_score == 1500
        assert new_user.level == 1
        assert new_user.xp == 0
        assert new_user.created_at is not None

        # Retrieve user
        query_result = await session.execute(select(User).where(User.telegram_id == test_tg_id))
        queried = query_result.scalar_one_or_none()
        assert queried is not None
        assert queried.first_name == "Diana"

        # Cleanup
        await session.delete(queried)
        await session.commit()
