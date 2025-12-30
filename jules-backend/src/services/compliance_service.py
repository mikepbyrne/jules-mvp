"""Compliance service for AI disclosure and regulatory requirements."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.logging import get_logger
from src.models.compliance import AIDisclosure
from src.models.user import User

settings = get_settings()
logger = get_logger(__name__)


class ComplianceService:
    """Service for regulatory compliance (NY AI Companion Law, CA SB 243)."""

    def __init__(self) -> None:
        """Initialize compliance service."""
        self.disclosure_interval_hours = settings.ai_disclosure_interval_hours
        self.disclosure_text = (
            "⚠️ IMPORTANT REMINDER: I'm Jules, an AI assistant. "
            "I'm here to help with practical life tasks, but I'm not a human, therapist, "
            "or medical professional. Our conversations are for informational purposes only."
        )

    async def check_disclosure_needed(
        self, db: AsyncSession, user_id: int, conversation_id: int
    ) -> bool:
        """
        Check if AI disclosure is needed based on time since last disclosure.

        Args:
            db: Database session
            user_id: User ID
            conversation_id: Conversation ID

        Returns:
            bool: True if disclosure is needed
        """
        # Get user's last disclosure
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return True

        # Check if disclosure is needed
        if not user.last_disclosure_at:
            return True

        time_since_disclosure = datetime.utcnow() - user.last_disclosure_at
        return time_since_disclosure >= timedelta(hours=self.disclosure_interval_hours)

    async def record_disclosure(
        self,
        db: AsyncSession,
        user_id: int,
        conversation_id: int,
        acknowledged: bool = False,
    ) -> AIDisclosure:
        """
        Record AI disclosure for compliance tracking.

        Args:
            db: Database session
            user_id: User ID
            conversation_id: Conversation ID
            acknowledged: Whether user acknowledged the disclosure

        Returns:
            AIDisclosure: Created disclosure record
        """
        disclosure = AIDisclosure(
            user_id=user_id,
            conversation_id=conversation_id,
            disclosure_text=self.disclosure_text,
            sent_at=datetime.utcnow(),
            acknowledged=acknowledged,
        )

        db.add(disclosure)

        # Update user's last disclosure time
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.last_disclosure_at = datetime.utcnow()

        await db.flush()

        logger.info(
            f"AI disclosure recorded",
            extra={
                "disclosure_id": disclosure.id,
                "user_id": user_id,
                "conversation_id": conversation_id,
            },
        )

        return disclosure

    def get_initial_disclosure(self) -> str:
        """Get disclosure message for first interaction."""
        return (
            "👋 Hi! I'm Jules, your AI life companion. "
            "I can help with grocery planning, reminders, decision-making, and daily tasks.\n\n"
            "⚠️ IMPORTANT: I'm an AI assistant, not a human, therapist, or medical professional. "
            "Our conversations are for informational and practical support only.\n\n"
            "Reply STOP anytime to unsubscribe."
        )

    def get_periodic_disclosure(self) -> str:
        """Get periodic disclosure message (every 3 hours)."""
        return self.disclosure_text

    async def check_minor_safety_requirements(
        self, db: AsyncSession, user_id: int, message_content: str
    ) -> dict[str, Any]:
        """
        Check if message violates minor safety requirements (CA SB 243).

        Args:
            db: Database session
            user_id: User ID
            message_content: Message content to check

        Returns:
            dict: Safety check results
        """
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_minor:
            return {"is_minor": False, "requires_filtering": False}

        # Check for sexual content keywords (basic implementation)
        sexual_keywords = [
            "sex",
            "sexual",
            "nude",
            "porn",
            "explicit",
            # Add more as needed
        ]

        contains_sexual_content = any(
            keyword in message_content.lower() for keyword in sexual_keywords
        )

        return {
            "is_minor": True,
            "requires_filtering": contains_sexual_content,
            "content_type": "sexual" if contains_sexual_content else "safe",
        }

    def get_minor_content_block_message(self) -> str:
        """Get message to send when content is blocked for minors."""
        return (
            "I can't respond to that type of message. "
            "Let's talk about something else I can help you with!"
        )


# Global compliance service instance
compliance_service = ComplianceService()


async def get_compliance_service() -> ComplianceService:
    """Dependency to get compliance service."""
    return compliance_service
