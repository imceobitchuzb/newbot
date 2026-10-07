import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, String, Text, Integer, JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.user import User


class TutorConversation(Base):
    __tablename__ = "tutor_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="GENERAL"
    )
    context_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", lazy="selectin")
    messages: Mapped[List["TutorMessage"]] = relationship(
        "TutorMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="TutorMessage.created_at",
        lazy="selectin",
    )


class TutorMessage(Base):
    __tablename__ = "tutor_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutor_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    actions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    conversation: Mapped["TutorConversation"] = relationship(
        "TutorConversation", back_populates="messages", lazy="selectin"
    )
