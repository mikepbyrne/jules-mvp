"""Compliance tracking models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class CrisisEventType(str, Enum):
    """Types of crisis events."""

    SUICIDE = "suicide"
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"
    ABUSE = "abuse"
    OTHER = "other"


class CrisisEvent(Base):
    """Crisis detection event log for compliance reporting."""

    __tablename__ = "crisis_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    conversation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=True
    )

    # Event details
    event_type: Mapped[CrisisEventType] = mapped_column(String(50), nullable=False)
    keywords_detected: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Response
    hotline_provided: Mapped[bool] = mapped_column(Boolean, default=False)
    hotline_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    user_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)

    # Anonymized for reporting (no PII)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class AIDisclosure(Base):
    """AI disclosure tracking for compliance."""

    __tablename__ = "ai_disclosures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"))

    # Disclosure details
    disclosure_text: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Base):
    """Audit log for sensitive operations."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Metadata
    metadata: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
