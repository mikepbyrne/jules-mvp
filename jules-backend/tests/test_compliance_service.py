"""
Compliance Service Tests
Tests for AI disclosure, opt-out handling, and regulatory compliance
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.compliance_service import ComplianceService, get_compliance_service
from src.models.user import User
from src.models.compliance import AIDisclosure, OptOutEvent


@pytest.mark.asyncio
class TestAIDisclosure:
    """Test AI disclosure requirements (NY AI Companion Law)"""

    async def test_ai_disclosure_on_session_start(self, db_session):
        """NY Law: AI disclosure required at session start"""
        compliance_service = ComplianceService()
        user = User(
            id=1,
            phone_number="+15551234567",
            created_at=datetime.utcnow()
        )

        # First message of session
        disclosure_required = await compliance_service.should_send_ai_disclosure(
            db=db_session,
            user=user,
            is_new_session=True
        )

        assert disclosure_required is True

    async def test_ai_disclosure_every_3_hours(self, db_session):
        """NY Law: AI disclosure every 3 hours of continuous use"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567")

        # Create disclosure 3+ hours ago
        old_disclosure = AIDisclosure(
            user_id=user.id,
            disclosed_at=datetime.utcnow() - timedelta(hours=3, minutes=5)
        )
        db_session.add(old_disclosure)
        await db_session.commit()

        # Should require new disclosure
        disclosure_required = await compliance_service.should_send_ai_disclosure(
            db=db_session,
            user=user,
            is_new_session=False
        )

        assert disclosure_required is True

    async def test_ai_disclosure_not_required_within_3_hours(self, db_session):
        """No disclosure needed if within 3-hour window"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567")

        # Create recent disclosure (2 hours ago)
        recent_disclosure = AIDisclosure(
            user_id=user.id,
            disclosed_at=datetime.utcnow() - timedelta(hours=2)
        )
        db_session.add(recent_disclosure)
        await db_session.commit()

        disclosure_required = await compliance_service.should_send_ai_disclosure(
            db=db_session,
            user=user,
            is_new_session=False
        )

        assert disclosure_required is False

    async def test_ai_disclosure_message_content(self):
        """Verify AI disclosure message contains required language"""
        compliance_service = ComplianceService()
        disclosure_message = compliance_service.get_ai_disclosure_message()

        # Should mention AI or artificial intelligence
        assert "AI" in disclosure_message or "artificial intelligence" in disclosure_message.lower()

        # Should be brief (SMS-appropriate)
        assert len(disclosure_message) <= 300

    async def test_ai_disclosure_tracking(self, db_session):
        """Verify AI disclosures are tracked in database"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567")
        db_session.add(user)
        await db_session.commit()

        # Record disclosure
        await compliance_service.record_ai_disclosure(
            db=db_session,
            user_id=user.id,
            message="I'm an AI assistant"
        )

        # Verify disclosure recorded
        disclosures = await db_session.execute(
            db_session.query(AIDisclosure).filter(
                AIDisclosure.user_id == user.id
            )
        )
        disclosure_list = disclosures.scalars().all()

        assert len(disclosure_list) == 1
        assert disclosure_list[0].user_id == user.id


@pytest.mark.asyncio
class TestOptOutHandling:
    """Test opt-out handling (TCPA compliance)"""

    async def test_stop_keyword_immediate_opt_out(self, db_session):
        """TCPA: STOP keyword immediately opts out user"""
        compliance_service = ComplianceService()
        user = User(
            id=1,
            phone_number="+15551234567",
            opt_in_status="active"
        )
        db_session.add(user)
        await db_session.commit()

        # Process STOP command
        result = await compliance_service.process_opt_out_request(
            db=db_session,
            user=user,
            message="STOP"
        )

        assert result["opted_out"] is True
        assert user.opt_in_status == "opted_out"

    async def test_opt_out_keywords_recognized(self, db_session):
        """Recognize all opt-out keywords: STOP, UNSUBSCRIBE, CANCEL, END, QUIT"""
        compliance_service = ComplianceService()
        keywords = ["STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT", "stop", "unsubscribe"]

        for keyword in keywords:
            user = User(
                id=1,
                phone_number="+15551234567",
                opt_in_status="active"
            )

            result = await compliance_service.process_opt_out_request(
                db=db_session,
                user=user,
                message=keyword
            )

            assert result["opted_out"] is True, f"Keyword '{keyword}' should trigger opt-out"

    async def test_opt_out_confirmation_message(self, db_session):
        """Verify opt-out confirmation message sent"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567", opt_in_status="active")

        result = await compliance_service.process_opt_out_request(
            db=db_session,
            user=user,
            message="STOP"
        )

        confirmation = result.get("confirmation_message")
        assert confirmation is not None
        assert "stopped" in confirmation.lower() or "unsubscribed" in confirmation.lower()

    async def test_opt_out_event_logged(self, db_session):
        """Verify opt-out events logged for audit trail"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567", opt_in_status="active")
        db_session.add(user)
        await db_session.commit()

        await compliance_service.process_opt_out_request(
            db=db_session,
            user=user,
            message="STOP"
        )

        # Verify opt-out event recorded
        events = await db_session.execute(
            db_session.query(OptOutEvent).filter(
                OptOutEvent.user_id == user.id
            )
        )
        event_list = events.scalars().all()

        assert len(event_list) == 1
        assert event_list[0].keyword_used == "STOP"

    async def test_opted_out_user_no_messages(self, db_session):
        """Verify opted-out users cannot receive messages"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567", opt_in_status="opted_out")

        can_send = await compliance_service.can_send_message(
            db=db_session,
            user=user
        )

        assert can_send is False

    async def test_opt_in_restart_keyword(self, db_session):
        """Allow users to opt back in with START keyword"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567", opt_in_status="opted_out")
        db_session.add(user)
        await db_session.commit()

        # Process START command
        result = await compliance_service.process_opt_in_request(
            db=db_session,
            user=user,
            message="START"
        )

        assert result["opted_in"] is True
        assert user.opt_in_status == "active"


@pytest.mark.asyncio
class TestMinorProtection:
    """Test minor protection (CA SB 243)"""

    async def test_minor_age_verification_required(self, db_session):
        """SB 243: Age verification required before enabling conversations"""
        compliance_service = ComplianceService()
        user = User(
            id=1,
            phone_number="+15551234567",
            age_verified=False,
            date_of_birth=None
        )

        can_converse = await compliance_service.can_enable_conversation(
            db=db_session,
            user=user
        )

        assert can_converse is False

    async def test_verified_adult_can_converse(self, db_session):
        """Verified adults can use conversation features"""
        compliance_service = ComplianceService()
        user = User(
            id=1,
            phone_number="+15551234567",
            age_verified=True,
            date_of_birth=datetime(1990, 1, 1)  # 35 years old
        )

        can_converse = await compliance_service.can_enable_conversation(
            db=db_session,
            user=user
        )

        assert can_converse is True

    async def test_sexual_content_blocked_for_minors(self, db_session):
        """SB 243: Sexual content prevention for known minors"""
        compliance_service = ComplianceService()

        # Simulate minor (15 years old)
        user = User(
            id=1,
            phone_number="+15551234567",
            age_verified=True,
            date_of_birth=datetime.utcnow() - timedelta(days=15*365)
        )

        # Content with sexual keywords
        message = "Let's talk about romantic relationships and intimacy"

        should_block = await compliance_service.should_block_content_for_minor(
            user=user,
            message=message
        )

        # Should flag for content filtering
        assert should_block is True


@pytest.mark.asyncio
class TestManipulationPrevention:
    """Test anti-manipulation design (CA SB 243)"""

    async def test_no_variable_reward_schedules(self):
        """SB 243: No variable reward schedules allowed"""
        compliance_service = ComplianceService()

        # Verify response patterns don't use randomized rewards
        # This is more of a design check than unit test
        # Implementation should be deterministic based on user input

        assert compliance_service.uses_variable_rewards() is False

    async def test_no_addictive_engagement_patterns(self):
        """Verify no addictive engagement patterns"""
        compliance_service = ComplianceService()

        # Check for absence of:
        # - Cliffhangers
        # - FOMO tactics
        # - Streak counters
        # - Achievement unlocks

        engagement_tactics = compliance_service.get_engagement_tactics()
        forbidden_tactics = ["variable_reward", "streak", "achievement", "fomo"]

        for tactic in forbidden_tactics:
            assert tactic not in engagement_tactics


@pytest.mark.asyncio
class TestConsentTracking:
    """Test express consent tracking (TCPA)"""

    async def test_express_consent_required(self, db_session):
        """TCPA: Express consent required before first message"""
        compliance_service = ComplianceService()
        user = User(
            id=1,
            phone_number="+15551234567",
            consent_given=False
        )

        can_send = await compliance_service.can_send_message(
            db=db_session,
            user=user
        )

        assert can_send is False

    async def test_consent_timestamp_recorded(self, db_session):
        """Verify consent timestamp recorded for audit"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567")
        db_session.add(user)
        await db_session.commit()

        await compliance_service.record_consent(
            db=db_session,
            user_id=user.id,
            consent_method="sms_opt_in"
        )

        assert user.consent_given is True
        assert user.consent_timestamp is not None

    async def test_consent_method_documented(self, db_session):
        """Document how consent was obtained"""
        compliance_service = ComplianceService()
        user = User(id=1, phone_number="+15551234567")
        db_session.add(user)
        await db_session.commit()

        await compliance_service.record_consent(
            db=db_session,
            user_id=user.id,
            consent_method="web_signup_checkbox"
        )

        assert user.consent_method == "web_signup_checkbox"


@pytest.mark.asyncio
class TestCrisisReferralTracking:
    """Test crisis referral tracking (CA SB 243 2027 reporting)"""

    async def test_crisis_referral_anonymized_logging(self, db_session):
        """SB 243: Log crisis referrals anonymously for annual reporting"""
        compliance_service = ComplianceService()

        # Simulate crisis detection
        await compliance_service.log_crisis_referral(
            db=db_session,
            trigger_keywords=["suicide", "end it all"],
            resource_provided="988 Suicide & Crisis Lifeline",
            anonymized_user_id="hash_abc123"  # No actual phone number stored
        )

        # Verify logged without PII
        referrals = await compliance_service.get_crisis_referral_stats(
            db=db_session,
            start_date=datetime.utcnow() - timedelta(days=1)
        )

        assert referrals["total_count"] == 1
        assert referrals["resource_988_count"] == 1
        # Verify no PII in logs
        assert "phone_number" not in str(referrals)
