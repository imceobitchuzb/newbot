from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin
from backend.app.models.enums import (
    Difficulty,
    QuestionStatus,
    QuestionType,
    Subject,
)

if TYPE_CHECKING:
    from backend.app.models.desmos import QuestionDesmosTechnique
    from backend.app.models.user import User


class Passage(Base, TimestampMixin):
    __tablename__ = "passages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    passage_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_info: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="passage",
    )

    def __repr__(self) -> str:
        return f"<Passage id={self.id} title={self.title}>"


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    passage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("passages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    skill: Mapped[str] = mapped_column(
        String(128),
        index=True,
        nullable=False,
    )
    subskill: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    question_type: Mapped[str] = mapped_column(
        String(32),
        default=QuestionType.MULTIPLE_CHOICE.value,
        nullable=False,
    )
    difficulty: Mapped[str] = mapped_column(
        String(16),
        index=True,
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    hint: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sat_shortcut: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    estimated_time_seconds: Mapped[int] = mapped_column(
        Integer,
        default=75,
        nullable=False,
    )
    desmos_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    desmos_recommended: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=QuestionStatus.PUBLISHED.value,
        index=True,
        nullable=False,
    )

    passage: Mapped[Optional["Passage"]] = relationship(
        "Passage",
        back_populates="questions",
    )
    options: Mapped[List["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.order_index",
        lazy="selectin",
    )
    attempts: Mapped[List["QuestionAttempt"]] = relationship(
        "QuestionAttempt",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    desmos_techniques: Mapped[List["QuestionDesmosTechnique"]] = relationship(
        "QuestionDesmosTechnique",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Question id={self.id} subject={self.subject} domain={self.domain} diff={self.difficulty}>"


class QuestionOption(Base):
    __tablename__ = "question_options"

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
    label: Mapped[str] = mapped_column(
        String(4),  # 'A', 'B', 'C', 'D'
        nullable=False,
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="options",
    )

    def __repr__(self) -> str:
        return f"<QuestionOption id={self.id} label={self.label} qid={self.question_id}>"


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

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
    selected_option_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("question_options.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    time_spent_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="attempts",
    )
    selected_option: Mapped["QuestionOption"] = relationship(
        "QuestionOption",
    )

    def __repr__(self) -> str:
        return f"<QuestionAttempt id={self.id} user={self.user_id} qid={self.question_id} correct={self.is_correct}>"
