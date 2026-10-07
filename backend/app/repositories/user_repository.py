import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.user import User


class UserRepository:
    async def get_by_id(self, db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        query = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.profile))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, db: AsyncSession, telegram_id: int) -> Optional[User]:
        query = (
            select(User)
            .where(User.telegram_id == telegram_id)
            .options(selectinload(User.profile))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        # Ensure profile is loaded
        return await self.get_by_id(db, user.id) or user

    async def update(self, db: AsyncSession, user: User) -> User:
        await db.commit()
        await db.refresh(user)
        return await self.get_by_id(db, user.id) or user


user_repository = UserRepository()
