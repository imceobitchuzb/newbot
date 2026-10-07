import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.profile import UserProfile


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    language_code: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    target_score: Mapped[int] = mapped_column(
        Integer,
        default=1400,
        nullable=False,
    )
    current_score_estimate: Mapped[int] = mapped_column(
        Integer,
        default=700,
        nullable=False,
    )
    math_estimate: Mapped[int] = mapped_column(
        Integer,
        default=360,
        nullable=False,
    )
    rw_estimate: Mapped[int] = mapped_column(
        Integer,
        default=340,
        nullable=False,
    )
    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} username={self.username} target={self.target_score}>"
