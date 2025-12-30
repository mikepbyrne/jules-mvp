"""User model."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TrustLevel(str, Enum):
    """User trust levels for security operations."""

    LEVEL_0 = "level_0"  # Phone number only
    LEVEL_1 = "level_1"  # + Payment verification
    LEVEL_2 = "level_2"  # + Security phrase
    LEVEL_3 = "level_3"  # + Email confirmation


class SubscriptionTier(str, Enum):
    """Subscription tiers."""

    FREE = "free"
    MONTHLY = "monthly"
    ANNUAL = "annual"


class User(Base):
    """User model with PII encryption."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    phone_number_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    # Basic info (encrypted)
    first_name_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Age verification
    age_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    age_verification_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_minor: Mapped[bool] = mapped_column(Boolean, default=False)

    # Subscription
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        String(20), default=SubscriptionTier.FREE
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Security
    trust_level: Mapped[TrustLevel] = mapped_column(String(20), default=TrustLevel.LEVEL_0)
    security_phrase_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Preferences (stored as JSON-like text, encrypted)
    preferences_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Compliance
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False)
    opted_out_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Session tracking
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_disclosure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
