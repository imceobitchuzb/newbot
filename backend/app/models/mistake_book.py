from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import (
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
from backend.app.models.enums import MistakeStatus, MistakeType

if TYPE_CHECKING:
    from backend.app.models.question import Question, QuestionAttempt
    from backend.app.models.user import User


class MistakeBookEntry(Base, TimestampMixin):
    __tablename__ = "mistake_book_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_mistake_book_user_question"),
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
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("question_attempts.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )
    domain: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    skill: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=MistakeStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    mistake_type: Mapped[str] = mapped_column(
        String(32),
        default=MistakeType.UNKNOWN.value,
        nullable=False,
    )
    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    correct_retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    incorrect_retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_review_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    question: Mapped["Question"] = relationship("Question")
    attempt: Mapped[Optional["QuestionAttempt"]] = relationship("QuestionAttempt")
