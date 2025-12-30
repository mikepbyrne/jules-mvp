"""Crisis detection and response service."""

import re
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.logging import get_logger
from src.models.compliance import CrisisEvent, CrisisEventType

settings = get_settings()
logger = get_logger(__name__)


class CrisisDetectionService:
    """Service for detecting and responding to crisis situations."""

    # Crisis keywords by category
    SUICIDE_KEYWORDS = [
        r"\bsuicide\b",
        r"\bkill myself\b",
        r"\bend (my|it all)\b",
        r"\bwant to die\b",
        r"\bdon'?t want to live\b",
        r"\bnot worth living\b",
        r"\bbetter off dead\b",
        r"\bsuicidal\b",
        r"\bending (it|my life)\b",
    ]

    SELF_HARM_KEYWORDS = [
        r"\bcut(ting)? myself\b",
        r"\bhurt(ing)? myself\b",
        r"\bself[- ]harm\b",
        r"\bbur(n|ning) myself\b",
        r"\bpunish myself\b",
    ]

    VIOLENCE_KEYWORDS = [
        r"\bhurt (someone|others|people)\b",
        r"\bkill (someone|others|people|them)\b",
        r"\bshoot (someone|others|people|them|up)\b",
        r"\battack (someone|others|people)\b",
        r"\bviolent thoughts\b",
    ]

    ABUSE_KEYWORDS = [
        r"\babusing me\b",
        r"\bhitting me\b",
        r"\bhurting me\b",
        r"\bafraid of\b",
        r"\bdom(estic)? violence\b",
    ]

    def __init__(self) -> None:
        """Initialize crisis detection service."""
        self.hotline_number = settings.crisis_hotline_number
        self.hotline_message = self._build_hotline_message()

    def _build_hotline_message(self) -> str:
        """Build crisis hotline referral message."""
        return (
            "I'm concerned about what you're sharing. Please know that help is available:\n\n"
            f"🆘 Crisis & Suicide Lifeline: {self.hotline_number}\n"
            "Available 24/7 for free, confidential support.\n\n"
            "You can also text 'HELLO' to 741741 for Crisis Text Line.\n\n"
            "I'm here to listen and support you, but I'm not a therapist or crisis counselor. "
            "These trained professionals can provide the immediate help you need."
        )

    async def detect_crisis(self, message: str) -> dict[str, Any]:
        """
        Detect crisis indicators in user message.

        Args:
            message: User message to analyze

        Returns:
            dict: Detection results with event_type, keywords, and confidence
        """
        message_lower = message.lower()
        detected_events = []

        # Check each category
        if self._check_keywords(message_lower, self.SUICIDE_KEYWORDS):
            detected_events.append(
                {
                    "type": CrisisEventType.SUICIDE,
                    "keywords": self._extract_matches(message_lower, self.SUICIDE_KEYWORDS),
                    "confidence": 0.9,
                }
            )

        if self._check_keywords(message_lower, self.SELF_HARM_KEYWORDS):
            detected_events.append(
                {
                    "type": CrisisEventType.SELF_HARM,
                    "keywords": self._extract_matches(message_lower, self.SELF_HARM_KEYWORDS),
                    "confidence": 0.8,
                }
            )

        if self._check_keywords(message_lower, self.VIOLENCE_KEYWORDS):
            detected_events.append(
                {
                    "type": CrisisEventType.VIOLENCE,
                    "keywords": self._extract_matches(message_lower, self.VIOLENCE_KEYWORDS),
                    "confidence": 0.85,
                }
            )

        if self._check_keywords(message_lower, self.ABUSE_KEYWORDS):
            detected_events.append(
                {
                    "type": CrisisEventType.ABUSE,
                    "keywords": self._extract_matches(message_lower, self.ABUSE_KEYWORDS),
                    "confidence": 0.75,
                }
            )

        if detected_events:
            # Return highest confidence event
            primary_event = max(detected_events, key=lambda x: x["confidence"])
            return {
                "detected": True,
                "event_type": primary_event["type"],
                "keywords": primary_event["keywords"],
                "confidence": primary_event["confidence"],
                "all_events": detected_events,
            }

        return {"detected": False}

    def _check_keywords(self, text: str, keywords: list[str]) -> bool:
        """Check if any keywords match in text."""
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in keywords)

    def _extract_matches(self, text: str, keywords: list[str]) -> list[str]:
        """Extract matched keywords from text."""
        matches = []
        for pattern in keywords:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matches.append(match.group(0))
        return matches

    async def log_crisis_event(
        self,
        db: AsyncSession,
        user_id: int,
        conversation_id: int | None,
        event_type: CrisisEventType,
        keywords: list[str],
        confidence: float,
        hotline_provided: bool = True,
    ) -> CrisisEvent:
        """
        Log crisis event for compliance reporting.

        Args:
            db: Database session
            user_id: User ID
            conversation_id: Conversation ID
            event_type: Type of crisis event
            keywords: Keywords detected
            confidence: Confidence score
            hotline_provided: Whether hotline info was provided

        Returns:
            CrisisEvent: Created event record
        """
        import json

        event = CrisisEvent(
            user_id=user_id,
            conversation_id=conversation_id,
            event_type=event_type,
            keywords_detected=json.dumps(keywords),
            confidence_score=confidence,
            hotline_provided=hotline_provided,
            hotline_number=self.hotline_number if hotline_provided else None,
            timestamp=datetime.utcnow(),
        )

        db.add(event)
        await db.flush()

        logger.warning(
            f"Crisis event logged",
            extra={
                "event_id": event.id,
                "event_type": event_type.value,
                "user_id": user_id,
                "confidence": confidence,
            },
        )

        return event

    def get_crisis_response(self) -> str:
        """Get the crisis response message with hotline information."""
        return self.hotline_message


# Global crisis service instance
crisis_service = CrisisDetectionService()


async def get_crisis_service() -> CrisisDetectionService:
    """Dependency to get crisis detection service."""
    return crisis_service
