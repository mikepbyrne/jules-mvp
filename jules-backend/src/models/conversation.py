"""Conversation and message models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class MessageRole(str, Enum):
    """Message role types."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageDirection(str, Enum):
    """Message direction (for SMS tracking)."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Conversation(Base):
    """Conversation session model."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)

    # Session tracking
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Metadata
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)


class Message(Base):
    """Message model with content encryption."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), index=True
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)

    # Message content (encrypted)
    content_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[MessageRole] = mapped_column(String(20), nullable=False)
    direction: Mapped[MessageDirection] = mapped_column(String(20), nullable=False)

    # SMS metadata
    sms_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sms_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # LLM metadata
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Safety flags
    crisis_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_flagged: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
