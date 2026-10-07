from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin
from backend.app.models.enums import (
    AdaptiveSessionStatus,
    Difficulty,
    RecommendationType,
    Subject,
)

if TYPE_CHECKING:
    from backend.app.models.question import Question, QuestionOption
    from backend.app.models.user import User


class AdaptiveProfile(Base, TimestampMixin):
    """Stores persistent adaptive engine state for a user in a given subject."""
    __tablename__ = "adaptive_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "subject", name="uq_adaptive_profile_user_subject"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(32),
        default=Subject.MATH.value,
        nullable=False,
        index=True,
    )
    current_difficulty: Mapped[str] = mapped_column(
        String(16),
        default=Difficulty.MEDIUM.value,
        nullable=False,
    )
    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_correct: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<AdaptiveProfile user={self.user_id} subject={self.subject} diff={self.current_difficulty}>"


class AdaptivePracticeSession(Base, TimestampMixin):
    """Tracks a multi-question adaptive practice test sequence."""
    __tablename__ = "adaptive_practice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(32),
        default=Subject.MATH.value,
        nullable=False,
        index=True,
    )
    current_question_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )
    current_difficulty: Mapped[str] = mapped_column(
        String(16),
        default=Difficulty.MEDIUM.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=AdaptiveSessionStatus.IN_PROGRESS.value,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User")
    questions: Mapped[List["AdaptivePracticeQuestion"]] = relationship(
        "AdaptivePracticeQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AdaptivePracticeQuestion.order_index",
    )

    def __repr__(self) -> str:
        return f"<AdaptivePracticeSession id={self.id} user={self.user_id} status={self.status}>"


class AdaptivePracticeQuestion(Base):
    """Tracks an assigned question within an adaptive practice session."""
    __tablename__ = "adaptive_practice_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "order_index", name="uq_adaptive_session_order"),
        UniqueConstraint("session_id", "question_id", name="uq_adaptive_session_question"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("adaptive_practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    difficulty_at_assignment: Mapped[str] = mapped_column(
        String(16),
        default=Difficulty.MEDIUM.value,
        nullable=False,
    )
    recommendation_type: Mapped[str] = mapped_column(
        String(64),
        default=RecommendationType.WEAK_SKILL.value,
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    is_answered: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    selected_option_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("question_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_correct: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )
    time_spent_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    answered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    session: Mapped["AdaptivePracticeSession"] = relationship(
        "AdaptivePracticeSession",
        back_populates="questions",
    )
    question: Mapped["Question"] = relationship("Question")
    selected_option: Mapped[Optional["QuestionOption"]] = relationship("QuestionOption")

    def __repr__(self) -> str:
        return f"<AdaptivePracticeQuestion id={self.id} session={self.session_id} order={self.order_index} answered={self.is_answered}>"
