"""Tests for crisis detection service."""

import pytest

from src.models.compliance import CrisisEventType
from src.services.crisis_service import CrisisDetectionService


@pytest.mark.asyncio
class TestCrisisDetectionService:
    """Test suite for crisis detection service."""

    def test_detect_suicide_keywords(self):
        """Test suicide keyword detection."""
        service = CrisisDetectionService()

        # Positive cases
        result = service.detect_crisis("I want to kill myself")
        assert result["detected"] is True
        assert result["event_type"] == CrisisEventType.SUICIDE
        assert result["confidence"] >= 0.8

        result = service.detect_crisis("I don't want to live anymore")
        assert result["detected"] is True

        # Negative case
        result = service.detect_crisis("I'm feeling tired today")
        assert result["detected"] is False

    def test_detect_self_harm_keywords(self):
        """Test self-harm keyword detection."""
        service = CrisisDetectionService()

        result = service.detect_crisis("I've been cutting myself")
        assert result["detected"] is True
        assert result["event_type"] == CrisisEventType.SELF_HARM

        result = service.detect_crisis("I keep hurting myself")
        assert result["detected"] is True

    def test_detect_violence_keywords(self):
        """Test violence keyword detection."""
        service = CrisisDetectionService()

        result = service.detect_crisis("I want to hurt someone")
        assert result["detected"] is True
        assert result["event_type"] == CrisisEventType.VIOLENCE

        result = service.detect_crisis("I'm going to shoot them")
        assert result["detected"] is True

    def test_detect_abuse_keywords(self):
        """Test abuse keyword detection."""
        service = CrisisDetectionService()

        result = service.detect_crisis("My partner keeps hitting me")
        assert result["detected"] is True
        assert result["event_type"] == CrisisEventType.ABUSE

    def test_no_detection(self):
        """Test messages without crisis indicators."""
        service = CrisisDetectionService()

        result = service.detect_crisis("What should I make for dinner?")
        assert result["detected"] is False

        result = service.detect_crisis("I'm feeling a bit down today")
        assert result["detected"] is False

    def test_multiple_keywords(self):
        """Test message with multiple crisis indicators."""
        service = CrisisDetectionService()

        result = service.detect_crisis("I want to kill myself and hurt others")
        assert result["detected"] is True
        # Should return highest confidence event
        assert result["event_type"] in [CrisisEventType.SUICIDE, CrisisEventType.VIOLENCE]
        assert "all_events" in result
        assert len(result["all_events"]) >= 2

    def test_case_insensitive(self):
        """Test detection is case-insensitive."""
        service = CrisisDetectionService()

        result = service.detect_crisis("I WANT TO KILL MYSELF")
        assert result["detected"] is True

        result = service.detect_crisis("Cutting Myself")
        assert result["detected"] is True

    async def test_log_crisis_event(self, db_session):
        """Test logging crisis events."""
        service = CrisisDetectionService()

        event = await service.log_crisis_event(
            db=db_session,
            user_id=1,
            conversation_id=1,
            event_type=CrisisEventType.SUICIDE,
            keywords=["kill myself"],
            confidence=0.9,
            hotline_provided=True,
        )

        assert event.id is not None
        assert event.user_id == 1
        assert event.event_type == CrisisEventType.SUICIDE
        assert event.confidence_score == 0.9
        assert event.hotline_provided is True
        assert event.hotline_number == "988"

    def test_get_crisis_response(self):
        """Test crisis response message."""
        service = CrisisDetectionService()

        response = service.get_crisis_response()

        assert "988" in response
        assert "crisis" in response.lower()
        assert "741741" in response  # Crisis Text Line

    def test_extract_matches(self):
        """Test keyword extraction."""
        service = CrisisDetectionService()

        text = "I want to kill myself and end it all"
        matches = service._extract_matches(text, service.SUICIDE_KEYWORDS)

        assert len(matches) >= 1
        assert any("kill myself" in m.lower() for m in matches)
