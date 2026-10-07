from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin
from backend.app.models.enums import MathPracticeSessionStatus

if TYPE_CHECKING:
    from backend.app.models.question import Question, QuestionAttempt, QuestionOption
    from backend.app.models.user import User


class MathPracticeSession(Base, TimestampMixin):
    __tablename__ = "math_practice_sessions"

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
    domain: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    difficulty: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
    )
    skill: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )
    current_question_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=MathPracticeSessionStatus.IN_PROGRESS.value,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    questions: Mapped[List["MathPracticeQuestion"]] = relationship(
        "MathPracticeQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MathPracticeQuestion.order_index",
    )


class MathPracticeQuestion(Base):
    __tablename__ = "math_practice_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "order_index", name="uq_math_practice_questions_session_order"),
        UniqueConstraint("session_id", "question_id", name="uq_math_practice_questions_session_question"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("math_practice_sessions.id", ondelete="CASCADE"),
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
    selected_option_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("question_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("question_attempts.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_answered: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["MathPracticeSession"] = relationship(
        "MathPracticeSession",
        back_populates="questions",
    )
    question: Mapped["Question"] = relationship("Question")
    selected_option: Mapped[Optional["QuestionOption"]] = relationship("QuestionOption")
    attempt: Mapped[Optional["QuestionAttempt"]] = relationship("QuestionAttempt")
