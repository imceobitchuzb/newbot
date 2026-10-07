import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.user import User


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    target_score: Mapped[int] = mapped_column(
        Integer,
        default=1400,
        nullable=False,
    )
    diagnostic_status: Mapped[str] = mapped_column(
        String(32),
        default="not_started",
        nullable=False,
    )
    study_goal: Mapped[str] = mapped_column(
        String(255),
        default="Score 1400+ in 4 months",
        nullable=False,
    )
    daily_goal_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )
    math_estimate: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    rw_estimate: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} diagnostic={self.diagnostic_status} target={self.target_score}>"
