"""Tests for conversation service."""

import pytest

from src.models.conversation import MessageDirection, MessageRole
from src.services.conversation_service import ConversationService


@pytest.mark.asyncio
class TestConversationService:
    """Test suite for conversation orchestrator."""

    async def test_process_inbound_message_new_user(
        self,
        db_session,
        mock_sms_service,
        mock_llm_service,
        mock_crisis_service,
        redis_client,
    ):
        """Test processing message from new user."""
        from src.services.compliance_service import ComplianceService
        from src.services.user_service import UserService

        user_service = UserService()
        compliance_service = ComplianceService()

        service = ConversationService(
            sms_service=mock_sms_service,
            llm_service=mock_llm_service,
            user_service=user_service,
            crisis_service=mock_crisis_service,
            compliance_service=compliance_service,
            redis_client=redis_client,
        )

        result = await service.process_inbound_message(
            db=db_session,
            from_number="+15551234567",
            message_body="Hello Jules!",
            message_sid="msg-123",
        )

        assert result["status"] == "success"
        assert result["user_id"] is not None
        assert result["conversation_id"] is not None
        assert result["response_sent"] is True

        # Verify SMS was sent
        mock_sms_service.send_message.assert_called()

        # Verify LLM was called
        mock_llm_service.generate_response.assert_called()

    async def test_process_inbound_message_existing_user(
        self,
        db_session,
        user_factory,
        mock_sms_service,
        mock_llm_service,
        mock_crisis_service,
        redis_client,
    ):
        """Test processing message from existing user."""
        from src.services.compliance_service import ComplianceService
        from src.services.user_service import UserService

        # Create existing user
        user = await user_factory(phone_number="+15551234567", consent_given=True)

        user_service = UserService()
        compliance_service = ComplianceService()

        service = ConversationService(
            sms_service=mock_sms_service,
            llm_service=mock_llm_service,
            user_service=user_service,
            crisis_service=mock_crisis_service,
            compliance_service=compliance_service,
            redis_client=redis_client,
        )

        result = await service.process_inbound_message(
            db=db_session,
            from_number="+15551234567",
            message_body="How are you?",
            message_sid="msg-456",
        )

        assert result["status"] == "success"
        assert result["user_id"] == user.id

    async def test_process_stop_command(
        self,
        db_session,
        user_factory,
        mock_sms_service,
        mock_llm_service,
        mock_crisis_service,
        redis_client,
    ):
        """Test STOP command handling."""
        from src.services.compliance_service import ComplianceService
        from src.services.user_service import UserService

        user = await user_factory(phone_number="+15551234567")

        user_service = UserService()
        compliance_service = ComplianceService()

        service = ConversationService(
            sms_service=mock_sms_service,
            llm_service=mock_llm_service,
            user_service=user_service,
            crisis_service=mock_crisis_service,
            compliance_service=compliance_service,
            redis_client=redis_client,
        )

        result = await service.process_inbound_message(
            db=db_session,
            from_number="+15551234567",
            message_body="STOP",
            message_sid="msg-stop",
        )

        assert result["status"] == "opted_out"

        # Verify opt-out message was sent
        mock_sms_service.send_message.assert_called()
        call_args = mock_sms_service.send_message.call_args[0]
        assert "unsubscribed" in call_args[1].lower()

        # Verify user is opted out
        await db_session.refresh(user)
        assert user.opted_out is True

    async def test_process_crisis_detection(
        self,
        db_session,
        user_factory,
        mock_sms_service,
        mock_llm_service,
        redis_client,
    ):
        """Test crisis detection during message processing."""
        from src.models.compliance import CrisisEventType
        from src.services.compliance_service import ComplianceService
        from src.services.crisis_service import CrisisDetectionService
        from src.services.user_service import UserService

        user = await user_factory(phone_number="+15551234567")

        # Real crisis service for this test
        crisis_service = CrisisDetectionService()
        user_service = UserService()
        compliance_service = ComplianceService()

        service = ConversationService(
            sms_service=mock_sms_service,
            llm_service=mock_llm_service,
            user_service=user_service,
            crisis_service=crisis_service,
            compliance_service=compliance_service,
            redis_client=redis_client,
        )

        result = await service.process_inbound_message(
            db=db_session,
            from_number="+15551234567",
            message_body="I want to kill myself",
            message_sid="msg-crisis",
        )

        assert result["status"] == "success"

        # Verify crisis message was sent
        assert mock_sms_service.send_message.call_count >= 2  # Crisis + normal response

    async def test_opted_out_user_ignored(
        self,
        db_session,
        user_factory,
        mock_sms_service,
        mock_llm_service,
        mock_crisis_service,
        redis_client,
    ):
        """Test messages from opted-out users are ignored."""
        from src.services.compliance_service import ComplianceService
        from src.services.user_service import UserService

        user = await user_factory(phone_number="+15551234567", opted_out=True)

        user_service = UserService()
        compliance_service = ComplianceService()

        service = ConversationService(
            sms_service=mock_sms_service,
            llm_service=mock_llm_service,
            user_service=user_service,
            crisis_service=mock_crisis_service,
            compliance_service=compliance_service,
            redis_client=redis_client,
        )

        result = await service.process_inbound_message(
            db=db_session,
            from_number="+15551234567",
            message_body="Hello",
            message_sid="msg-ignored",
        )

        assert result["status"] == "ignored"
        assert result["reason"] == "user_opted_out"

        # No SMS should be sent
        mock_sms_service.send_message.assert_not_called()

    async def test_conversation_history_context(
        self,
        db_session,
        user_factory,
        conversation_factory,
        message_factory,
        mock_sms_service,
        mock_llm_service,
        mock_crisis_service,
        redis_client,
    ):
        """Test conversation history is passed as context."""
        from src.services.compliance_service import ComplianceService
        from src.services.user_service import UserService

        user = await user_factory(phone_number="+15551234567")
        conversation = await conversation_factory(user_id=user.id)

        # Create some message history
        await message_factory(
            conversation_id=conversation.id,
            user_id=user.id,
            content="Hello",
            role=MessageRole.USER,
        )
        await message_factory(
            conversation_id=conversation.id,
            user_id=user.id,
            content="Hi! How can I help?",
            role=MessageRole.ASSISTANT,
        )

        user_service = UserService()
        compliance_service = ComplianceService()

        service = ConversationService(
            sms_service=mock_sms_service,
            llm_service=mock_llm_service,
            user_service=user_service,
            crisis_service=mock_crisis_service,
            compliance_service=compliance_service,
            redis_client=redis_client,
        )

        await service.process_inbound_message(
            db=db_session,
            from_number="+15551234567",
            message_body="What's the weather?",
            message_sid="msg-history",
        )

        # Verify LLM was called with message history
        mock_llm_service.generate_response.assert_called()
        call_kwargs = mock_llm_service.generate_response.call_args[1]
        messages = call_kwargs["messages"]

        # Should include previous messages
        assert len(messages) >= 3  # Previous 2 + new one
