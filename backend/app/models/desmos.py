from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin
from backend.app.models.enums import DesmosSessionStatus, Difficulty, Subject

if TYPE_CHECKING:
    from backend.app.models.question import Question, QuestionAttempt, QuestionOption
    from backend.app.models.user import User


class DesmosTechnique(Base, TimestampMixin):
    __tablename__ = "desmos_techniques"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    technique_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    subject: Mapped[str] = mapped_column(
        String(32),
        default=Subject.MATH.value,
        nullable=False,
    )
    difficulty: Mapped[str] = mapped_column(
        String(16),
        default=Difficulty.MEDIUM.value,
        nullable=False,
    )
    when_to_use: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    when_not_to_use: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    steps: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    common_mistakes: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    sat_tip: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    example_question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    example_question: Mapped[Optional["Question"]] = relationship(
        "Question",
        foreign_keys=[example_question_id],
    )
    question_links: Mapped[List["QuestionDesmosTechnique"]] = relationship(
        "QuestionDesmosTechnique",
        back_populates="technique",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DesmosTechnique slug={self.slug} title={self.title}>"


class QuestionDesmosTechnique(Base, TimestampMixin):
    __tablename__ = "question_desmos_techniques"
    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "technique_id",
            name="uq_question_desmos_technique",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technique_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("desmos_techniques.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technique_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    question: Mapped["Question"] = relationship(
        "Question",
        foreign_keys=[question_id],
    )
    technique: Mapped["DesmosTechnique"] = relationship(
        "DesmosTechnique",
        back_populates="question_links",
    )


class DesmosPracticeSession(Base, TimestampMixin):
    __tablename__ = "desmos_practice_sessions"

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
    technique_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("desmos_techniques.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    technique_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    difficulty: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
    )
    target_count: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )
    completed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    correct_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=DesmosSessionStatus.IN_PROGRESS.value,
        index=True,
        nullable=False,
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

    # Relationships
    user: Mapped["User"] = relationship("User")
    technique: Mapped[Optional["DesmosTechnique"]] = relationship(
        "DesmosTechnique",
        foreign_keys=[technique_id],
        lazy="selectin",
    )
    questions: Mapped[List["DesmosPracticeQuestion"]] = relationship(
        "DesmosPracticeQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DesmosPracticeQuestion.order_index",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<DesmosPracticeSession id={self.id} user={self.user_id} status={self.status}>"


class DesmosPracticeQuestion(Base, TimestampMixin):
    __tablename__ = "desmos_practice_questions"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "order_index",
            name="uq_desmos_session_order",
        ),
        UniqueConstraint(
            "session_id",
            "question_id",
            name="uq_desmos_session_question",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("desmos_practice_sessions.id", ondelete="CASCADE"),
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
    technique_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
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
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    desmos_used: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    answered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    session: Mapped["DesmosPracticeSession"] = relationship(
        "DesmosPracticeSession",
        back_populates="questions",
    )
    question: Mapped["Question"] = relationship("Question", lazy="selectin")
    selected_option: Mapped[Optional["QuestionOption"]] = relationship("QuestionOption", lazy="selectin")
    attempt: Mapped[Optional["QuestionAttempt"]] = relationship("QuestionAttempt", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DesmosPracticeQuestion session={self.session_id} q={self.question_id} order={self.order_index}>"
