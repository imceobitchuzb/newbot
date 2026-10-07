from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin
from backend.app.models.enums import (
    DiagnosticModuleStatus,
    DiagnosticStatus,
    Subject,
)

if TYPE_CHECKING:
    from backend.app.models.question import Question, QuestionAttempt, QuestionOption
    from backend.app.models.user import User


class DiagnosticSession(Base, TimestampMixin):
    __tablename__ = "diagnostic_sessions"

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
    status: Mapped[str] = mapped_column(
        String(32),
        default=DiagnosticStatus.IN_PROGRESS.value,
        nullable=False,
        index=True,
    )
    current_module: Mapped[str] = mapped_column(
        String(32),
        default=Subject.MATH.value,
        nullable=False,
    )
    current_question_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
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
    modules: Mapped[List["DiagnosticModule"]] = relationship(
        "DiagnosticModule",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DiagnosticModule.module_number",
    )
    result: Mapped[Optional["DiagnosticResult"]] = relationship(
        "DiagnosticResult",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DiagnosticModule(Base):
    __tablename__ = "diagnostic_modules"
    __table_args__ = (
        UniqueConstraint("session_id", "module_number", name="uq_diagnostic_modules_session_module_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    module_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=DiagnosticModuleStatus.NOT_STARTED.value,
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["DiagnosticSession"] = relationship(
        "DiagnosticSession",
        back_populates="modules",
    )
    questions: Mapped[List["DiagnosticQuestion"]] = relationship(
        "DiagnosticQuestion",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="DiagnosticQuestion.order_index",
    )


class DiagnosticQuestion(Base):
    __tablename__ = "diagnostic_questions"
    __table_args__ = (
        UniqueConstraint("module_id", "order_index", name="uq_diagnostic_questions_module_order"),
        UniqueConstraint("module_id", "question_id", name="uq_diagnostic_questions_module_question"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("diagnostic_modules.id", ondelete="CASCADE"),
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

    # Relationships
    module: Mapped["DiagnosticModule"] = relationship(
        "DiagnosticModule",
        back_populates="questions",
    )
    question: Mapped["Question"] = relationship("Question")
    selected_option: Mapped[Optional["QuestionOption"]] = relationship("QuestionOption")
    attempt: Mapped[Optional["QuestionAttempt"]] = relationship("QuestionAttempt")


class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    math_correct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    math_total: Mapped[int] = mapped_column(
        Integer,
        default=20,
        nullable=False,
    )
    rw_correct: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    rw_total: Mapped[int] = mapped_column(
        Integer,
        default=20,
        nullable=False,
    )
    math_accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    rw_accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    total_accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    estimated_math_low: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    estimated_math_high: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    estimated_rw_low: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    estimated_rw_high: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    estimated_total_low: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    estimated_total_high: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    domain_breakdown: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
    )
    weak_domains: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
    )
    strong_domains: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["DiagnosticSession"] = relationship(
        "DiagnosticSession",
        back_populates="result",
    )
