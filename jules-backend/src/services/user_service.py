"""User management service."""

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.security import decrypt_data, encrypt_data
from src.models.user import SubscriptionTier, TrustLevel, User

logger = get_logger(__name__)


class UserService:
    """Service for user management with PII encryption."""

    async def get_or_create_user(
        self, db: AsyncSession, phone_number: str, first_name: str | None = None
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one.

        Args:
            db: Database session
            phone_number: User's phone number (E.164 format)
            first_name: Optional first name

        Returns:
            tuple: (User, created) where created is True if user was created
        """
        # Check if user exists
        stmt = select(User).where(User.phone_number == phone_number)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return user, False

        # Create new user with encryption
        user = User(
            phone_number=phone_number,
            phone_number_encrypted=encrypt_data(phone_number),
            first_name_encrypted=encrypt_data(first_name) if first_name else None,
            trust_level=TrustLevel.LEVEL_0,
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
        )

        db.add(user)
        await db.flush()

        logger.info(f"New user created", extra={"user_id": user.id})

        return user, True

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_phone(self, db: AsyncSession, phone_number: str) -> User | None:
        """Get user by phone number."""
        stmt = select(User).where(User.phone_number == phone_number)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_stripe_customer(
        self, db: AsyncSession, customer_id: str
    ) -> User | None:
        """Get user by Stripe customer ID."""
        stmt = select(User).where(User.stripe_customer_id == customer_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    def get_decrypted_first_name(self, user: User) -> str | None:
        """Get decrypted first name from user."""
        if user.first_name_encrypted:
            try:
                return decrypt_data(user.first_name_encrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt first name: {e}")
                return None
        return None

    def get_decrypted_phone(self, user: User) -> str:
        """Get decrypted phone number from user."""
        return decrypt_data(user.phone_number_encrypted)

    async def update_preferences(
        self, db: AsyncSession, user: User, preferences: dict
    ) -> User:
        """
        Update user preferences with encryption.

        Args:
            db: Database session
            user: User to update
            preferences: Preferences dict to store

        Returns:
            User: Updated user
        """
        user.preferences_encrypted = encrypt_data(json.dumps(preferences))
        await db.flush()
        return user

    def get_decrypted_preferences(self, user: User) -> dict:
        """Get decrypted user preferences."""
        if user.preferences_encrypted:
            try:
                decrypted = decrypt_data(user.preferences_encrypted)
                return json.loads(decrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt preferences: {e}")
                return {}
        return {}

    async def update_last_message_time(
        self, db: AsyncSession, user: User
    ) -> User:
        """Update user's last message timestamp."""
        user.last_message_at = datetime.utcnow()
        user.message_count += 1
        await db.flush()
        return user

    async def verify_age(
        self, db: AsyncSession, user: User, is_minor: bool = False
    ) -> User:
        """
        Mark user as age verified.

        Args:
            db: Database session
            user: User to verify
            is_minor: Whether user is a minor

        Returns:
            User: Updated user
        """
        user.age_verified = True
        user.age_verification_timestamp = datetime.utcnow()
        user.is_minor = is_minor
        await db.flush()

        logger.info(
            f"User age verified",
            extra={"user_id": user.id, "is_minor": is_minor},
        )

        return user

    async def update_subscription(
        self,
        db: AsyncSession,
        user: User,
        tier: SubscriptionTier,
        stripe_customer_id: str | None = None,
        status: str | None = None,
        expires_at: datetime | None = None,
    ) -> User:
        """Update user subscription details."""
        user.subscription_tier = tier
        if stripe_customer_id:
            user.stripe_customer_id = stripe_customer_id
        if status:
            user.subscription_status = status
        if expires_at:
            user.subscription_expires_at = expires_at

        # Upgrade trust level when payment verified
        if tier != SubscriptionTier.FREE and user.trust_level == TrustLevel.LEVEL_0:
            user.trust_level = TrustLevel.LEVEL_1

        await db.flush()
        return user

    async def opt_out_user(self, db: AsyncSession, user: User) -> User:
        """Mark user as opted out."""
        user.opted_out = True
        user.opted_out_timestamp = datetime.utcnow()
        await db.flush()

        logger.info(f"User opted out", extra={"user_id": user.id})

        return user


# Global user service instance
user_service = UserService()


async def get_user_service() -> UserService:
    """Dependency to get user service."""
    return user_service
