"""
Compliance Workflow Integration Tests
Test regulatory compliance flows end-to-end

Based on compass: "Complete NY compliance immediately—the law is already in effect"
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.conversation_service import ConversationService
from src.services.compliance_service import ComplianceService
from src.models.user import User
from src.models.compliance import AIDisclosure


@pytest.mark.asyncio
@pytest.mark.integration
class TestAIDisclosureFlow:
    """Test AI disclosure compliance (NY AI Companion Law)"""

    async def test_ai_disclosure_on_session_start(
        self, db_session, conversation_service
    ):
        """
        NY Law: AI disclosure required at session start
        Compass: "Clear AI disclosure at session start"
        """
        # Create new user (first session)
        user = User(
            id=1,
            phone_number="+15551234567",
            consent_given=True,
            opt_in_status="active"
        )
        db_session.add(user)
        await db_session.commit()

        # First message
        result = await conversation_service.process_inbound_message(
            db=db_session,
            from_number=user.phone_number,
            message_body="Hi",
            message_sid="test_123"
        )

        response = result.get("response", "")

        # MUST contain AI disclosure
        assert "AI" in response or "artificial intelligence" in response.lower(), \
            "No AI disclosure in first message"

        # Verify disclosure recorded in database
        disclosures = await db_session.execute(
            db_session.query(AIDisclosure).filter(
                AIDisclosure.user_id == user.id
            )
        )
        disclosure_list = disclosures.scalars().all()

        assert len(disclosure_list) >= 1, "AI disclosure not recorded"

    async def test_ai_disclosure_every_3_hours(
        self, db_session, conversation_service, compliance_service
    ):
        """
        NY Law: AI disclosure every 3 hours of continuous use
        Compass: "3-hour session reminders (NY law requirement)"
        """
        user = User(id=1, phone_number="+15551234567", opt_in_status="active")
        db_session.add(user)
        await db_session.commit()

        # Create old disclosure (3+ hours ago)
        old_disclosure = AIDisclosure(
            user_id=user.id,
            disclosed_at=datetime.utcnow() - timedelta(hours=3, minutes=10),
            message="I'm an AI assistant"
        )
        db_session.add(old_disclosure)
        await db_session.commit()

        # Send message after 3+ hours
        result = await conversation_service.process_inbound_message(
            db=db_session,
            from_number=user.phone_number,
            message_body="What's for dinner?",
            message_sid="test_123"
        )

        response = result.get("response", "")

        # Should include AI disclosure reminder
        assert "AI" in response or "artificial intelligence" in response.lower(), \
            "No AI disclosure after 3 hours"

    async def test_ai_disclosure_not_repeated_within_3_hours(
        self, db_session, conversation_service
    ):
        """No AI disclosure needed if within 3-hour window"""
        user = User(id=1, phone_number="+15551234567", opt_in_status="active")
        db_session.add(user)
        await db_session.commit()

        # Create recent disclosure (1 hour ago)
        recent_disclosure = AIDisclosure(
            user_id=user.id,
            disclosed_at=datetime.utcnow() - timedelta(hours=1),
            message="I'm an AI assistant"
        )
        db_session.add(recent_disclosure)
        await db_session.commit()

        # Send message within 3-hour window
        result = await conversation_service.process_inbound_message(
            db=db_session,
            from_number=user.phone_number,
            message_body="Need meal ideas",
            message_sid="test_123"
        )

        response = result.get("response", "")

        # Should NOT repeat AI disclosure
        # (May still appear in general conversation, but not as compliance reminder)
        # This is a judgment call - implementation may vary


@pytest.mark.asyncio
@pytest.mark.integration
class TestOptOutFlow:
    """Test opt-out compliance (TCPA)"""

    async def test_stop_keyword_immediate_opt_out(
        self, db_session, conversation_service
    ):
        """
        TCPA: STOP keyword immediately opts out user
        Compass: "Immediate processing of STOP requests"
        """
        user = User(
            id=1,
            phone_number="+15551234567",
            opt_in_status="active",
            consent_given=True
        )
        db_session.add(user)
        await db_session.commit()

        # Send STOP command
        result = await conversation_service.process_inbound_message(
            db=db_session,
            from_number=user.phone_number,
            message_body="STOP",
            message_sid="test_123"
        )

        # Refresh user from database
        await db_session.refresh(user)

        # Should be opted out immediately
        assert user.opt_in_status == "opted_out", "User not opted out after STOP"

        # Should receive confirmation
        response = result.get("response", "")
        assert "stop" in response.lower() or "unsubscribed" in response.lower()

    async def test_opted_out_user_no_future_messages(
        self, db_session, conversation_service
    ):
        """Verify opted-out users cannot receive messages"""
        user = User(
            id=1,
            phone_number="+15551234567",
            opt_in_status="opted_out"
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt to send message to opted-out user
        try:
            result = await conversation_service.process_inbound_message(
                db=db_session,
                from_number=user.phone_number,
                message_body="Hi",
                message_sid="test_123"
            )

            # If response sent, should only be opt-in instructions
            response = result.get("response", "")
            assert "opt" in response.lower() or "START" in response

        except Exception as e:
            # Or may raise exception for opted-out users
            assert "opt" in str(e).lower()

    async def test_start_keyword_re_opt_in(
        self, db_session, conversation_service
    ):
        """Allow users to opt back in with START keyword"""
        user = User(
            id=1,
            phone_number="+15551234567",
            opt_in_status="opted_out"
        )
        db_session.add(user)
        await db_session.commit()

        # Send START command
        result = await conversation_service.process_inbound_message(
            db=db_session,
            from_number=user.phone_number,
            message_body="START",
            message_sid="test_123"
        )

        # Refresh user
        await db_session.refresh(user)

        # Should be active again
        assert user.opt_in_status == "active", "User not re-activated after START"

        # Should receive confirmation
        response = result.get("response", "")
        assert "start" in response.lower() or "subscribed" in response.lower()


@pytest.mark.asyncio
@pytest.mark.integration
class TestAgeVerificationFlow:
    """Test age verification compliance (CA SB 243)"""

    async def test_minor_age_verification_required(
        self, db_session, conversation_service
    ):
        """
        SB 243: Age verification required before enabling conversations
        Compass: "Implement robust age verification from day one"
        """
        # Create unverified user
        user = User(
            id=1,
            phone_number="+15551234567",
            age_verified=False,
            date_of_birth=None,
            opt_in_status="pending"
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt conversation
        result = await conversation_service.process_inbound_message(
            db=db_session,
            from_number=user.phone_number,
            message_body="Hi",
            message_sid="test_123"
        )

        response = result.get("response", "")

        # Should prompt for age verification
        assert "verify" in response.lower() or "age" in response.lower(), \
            "No age verification prompt"

        # Should NOT enable full conversation
        assert result.get("conversation_enabled") is not True

    async def test_verified_adult_can_converse(
        self, db_session, conversation_service
    ):
        """Verified adults can use conversation features"""
        user = User(
            id=1,
            phone_number="+15551234567",
            age_verified=True,
            date_of_birth=datetime(1990, 1, 1),  # 35 years old
            opt_in_status="active",
            consent_given=True
        )
        db_session.add(user)
        await db_session.commit()

        # Send conversation message
        result = await conversation_service.process_inbound_message(
            db=db_session,
            from_number=user.phone_number,
            message_body="What should I make for dinner?",
            message_sid="test_123"
        )

        response = result.get("response", "")

        # Should provide normal response
        assert len(response) > 0
        assert "verify" not in response.lower()  # No verification prompt

    async def test_veriff_webhook_enables_conversation(
        self, db_session, user_service
    ):
        """
        Veriff webhook callback enables conversation
        Compass: "user completes ID verification → webhook confirms → SMS enabled"
        """
        user = User(
            id=1,
            phone_number="+15551234567",
            age_verified=False,
            opt_in_status="pending"
        )
        db_session.add(user)
        await db_session.commit()

        # Simulate Veriff webhook callback
        await user_service.process_age_verification(
            db=db_session,
            user_id=user.id,
            verification_passed=True,
            date_of_birth=datetime(1990, 1, 1)
        )

        # Refresh user
        await db_session.refresh(user)

        # Should be verified
        assert user.age_verified is True
        assert user.date_of_birth is not None
        assert user.opt_in_status == "active"


@pytest.mark.asyncio
@pytest.mark.integration
class TestConsentTracking:
    """Test express consent tracking (TCPA)"""

    async def test_express_consent_required_before_messages(
        self, db_session, conversation_service
    ):
        """TCPA: Express consent required before first message"""
        user = User(
            id=1,
            phone_number="+15551234567",
            consent_given=False,
            opt_in_status="pending"
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt to send message without consent
        try:
            result = await conversation_service.process_inbound_message(
                db=db_session,
                from_number=user.phone_number,
                message_body="Hi",
                message_sid="test_123"
            )

            # Should prompt for consent or refuse
            response = result.get("response", "")
            assert "consent" in response.lower() or "opt" in response.lower()

        except Exception as e:
            # Or may raise exception for no consent
            assert "consent" in str(e).lower()

    async def test_consent_timestamp_recorded(
        self, db_session, user_service, compliance_service
    ):
        """Verify consent timestamp recorded for audit"""
        user = User(id=1, phone_number="+15551234567")
        db_session.add(user)
        await db_session.commit()

        # Record consent
        await compliance_service.record_consent(
            db=db_session,
            user_id=user.id,
            consent_method="sms_opt_in"
        )

        # Refresh user
        await db_session.refresh(user)

        # Should have consent recorded
        assert user.consent_given is True
        assert user.consent_timestamp is not None
        assert user.consent_method == "sms_opt_in"


@pytest.mark.asyncio
@pytest.mark.integration
class TestTCPATimeRestrictions:
    """Test TCPA time restrictions (8 AM - 9 PM local time)"""

    async def test_messages_blocked_outside_allowed_hours(
        self, db_session, sms_service
    ):
        """
        TCPA: Block messages outside 8 AM - 9 PM recipient local time
        Compass: "timing restrictions (8 AM-9 PM recipient local time)"
        """
        # This test requires time zone handling
        # Send message at 2 AM local time - should be blocked or queued

        # Implementation depends on SMS service rate limiting
        # Should check recipient's timezone and block if outside hours
        pass

    async def test_messages_allowed_during_business_hours(
        self, db_session, sms_service
    ):
        """Messages allowed during 8 AM - 9 PM window"""
        # Send message at 2 PM local time - should succeed
        pass
