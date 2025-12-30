"""Conversation orchestrator - main business logic."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.logging import get_logger
from src.core.redis import RedisClient
from src.core.security import encrypt_data, redact_phone_number
from src.models.conversation import Conversation, Message, MessageDirection, MessageRole
from src.models.user import User
from src.services.compliance_service import ComplianceService
from src.services.crisis_service import CrisisDetectionService
from src.services.llm_service import LLMService
from src.services.sms_service import SMSService
from src.services.user_service import UserService

settings = get_settings()
logger = get_logger(__name__)


class ConversationService:
    """Main conversation orchestrator coordinating all services."""

    def __init__(
        self,
        sms_service: SMSService,
        llm_service: LLMService,
        user_service: UserService,
        crisis_service: CrisisDetectionService,
        compliance_service: ComplianceService,
        redis_client: RedisClient,
    ) -> None:
        """Initialize conversation service with dependencies."""
        self.sms = sms_service
        self.llm = llm_service
        self.user_service = user_service
        self.crisis = crisis_service
        self.compliance = compliance_service
        self.redis = redis_client

    async def process_inbound_message(
        self, db: AsyncSession, from_number: str, message_body: str, message_sid: str
    ) -> dict[str, Any]:
        """
        Process inbound SMS message through full pipeline.

        Args:
            db: Database session
            from_number: Sender phone number
            message_body: Message content
            message_sid: Twilio/Bandwidth message ID

        Returns:
            dict: Processing result
        """
        try:
            # 1. Get or create user
            user, is_new = await self.user_service.get_or_create_user(db, from_number)

            # 2. Check opt-out status
            if user.opted_out:
                logger.info(f"Message from opted-out user", extra={"user_id": user.id})
                return {"status": "ignored", "reason": "user_opted_out"}

            # 3. Handle STOP command
            if message_body.strip().upper() in ["STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
                await self.user_service.opt_out_user(db, user)
                await self.sms.send_message(
                    from_number,
                    "You've been unsubscribed from Jules. "
                    "Reply START to resubscribe anytime.",
                )
                return {"status": "opted_out"}

            # 4. Check if disclosure needed
            conversation = await self._get_or_create_conversation(db, user.id)
            disclosure_needed = await self.compliance.check_disclosure_needed(
                db, user.id, conversation.id
            )

            # 5. Crisis detection
            crisis_result = await self.crisis.detect_crisis(message_body)
            if crisis_result.get("detected"):
                await self._handle_crisis(db, user, conversation, crisis_result)
                # Send crisis response and still continue conversation
                await self.sms.send_message(
                    from_number, self.crisis.get_crisis_response()
                )

            # 6. Save inbound message
            await self._save_message(
                db=db,
                conversation_id=conversation.id,
                user_id=user.id,
                content=message_body,
                role=MessageRole.USER,
                direction=MessageDirection.INBOUND,
                sms_message_id=message_sid,
                crisis_detected=crisis_result.get("detected", False),
            )

            # 7. Get conversation history for context
            messages = await self._get_recent_messages(db, conversation.id, limit=10)

            # 8. Generate AI response
            system_prompt = self._build_system_prompt(user)
            ai_response = await self.llm.generate_response(
                messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
                system_prompt=system_prompt,
            )

            response_text = ai_response["content"]

            # 9. Prepend disclosure if needed
            if disclosure_needed:
                disclosure_text = (
                    self.compliance.get_initial_disclosure()
                    if is_new
                    else self.compliance.get_periodic_disclosure()
                )
                response_text = f"{disclosure_text}\n\n{response_text}"
                await self.compliance.record_disclosure(db, user.id, conversation.id)

            # 10. Send response
            await self.sms.send_message(from_number, response_text)

            # 11. Save outbound message
            await self._save_message(
                db=db,
                conversation_id=conversation.id,
                user_id=user.id,
                content=response_text,
                role=MessageRole.ASSISTANT,
                direction=MessageDirection.OUTBOUND,
                model_used=ai_response.get("model"),
                tokens_used=ai_response.get("tokens_used"),
                latency_ms=ai_response.get("latency_ms"),
            )

            # 12. Update user activity
            await self.user_service.update_last_message_time(db, user)
            await db.commit()

            return {
                "status": "success",
                "user_id": user.id,
                "conversation_id": conversation.id,
                "response_sent": True,
            }

        except Exception as e:
            logger.error(
                f"Error processing message",
                extra={"from_number": from_number, "error": str(e)},
                exc_info=True,
            )
            await db.rollback()
            raise

    async def _get_or_create_conversation(
        self, db: AsyncSession, user_id: int
    ) -> Conversation:
        """Get or create active conversation session."""
        import uuid

        # Check for active conversation
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.ended_at.is_(None))
            .order_by(Conversation.last_activity_at.desc())
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            return conversation

        # Create new conversation
        conversation = Conversation(
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            started_at=datetime.utcnow(),
        )
        db.add(conversation)
        await db.flush()
        return conversation

    async def _save_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        content: str,
        role: MessageRole,
        direction: MessageDirection,
        sms_message_id: str | None = None,
        model_used: str | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
        crisis_detected: bool = False,
    ) -> Message:
        """Save message to database with encryption."""
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            content_encrypted=encrypt_data(content),
            role=role,
            direction=direction,
            sms_message_id=sms_message_id,
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            crisis_detected=crisis_detected,
        )
        db.add(message)
        await db.flush()
        return message

    async def _get_recent_messages(
        self, db: AsyncSession, conversation_id: int, limit: int = 10
    ) -> list[dict[str, str]]:
        """Get recent messages from conversation for context."""
        from src.core.security import decrypt_data

        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        # Reverse to chronological order
        messages = list(reversed(messages))

        return [
            {
                "role": msg.role.value,
                "content": decrypt_data(msg.content_encrypted),
            }
            for msg in messages
        ]

    def _build_system_prompt(self, user: User) -> str:
        """Build system prompt for LLM based on user context."""
        first_name = self.user_service.get_decrypted_first_name(user)
        name_part = f" You can call them {first_name}." if first_name else ""

        return f"""You are Jules, a helpful AI life companion assistant. You communicate via SMS, so keep responses concise and friendly.

Your role:
- Help with grocery planning, meal decisions, scheduling, and daily tasks
- Provide practical advice and support
- Be warm, conversational, and helpful

Important guidelines:
- Keep responses under 160 characters when possible (SMS limit)
- Be conversational and natural
- You are NOT a therapist, doctor, or crisis counselor
- For emergencies, direct users to appropriate services (988 for crisis, 911 for emergencies)
- Respect user privacy and be trustworthy

The user's phone number is registered.{name_part}
"""

    async def _handle_crisis(
        self,
        db: AsyncSession,
        user: User,
        conversation: Conversation,
        crisis_result: dict[str, Any],
    ) -> None:
        """Handle detected crisis situation."""
        await self.crisis.log_crisis_event(
            db=db,
            user_id=user.id,
            conversation_id=conversation.id,
            event_type=crisis_result["event_type"],
            keywords=crisis_result["keywords"],
            confidence=crisis_result["confidence"],
            hotline_provided=True,
        )


async def get_conversation_service(
    sms_service: SMSService,
    llm_service: LLMService,
    user_service: UserService,
    crisis_service: CrisisDetectionService,
    compliance_service: ComplianceService,
    redis_client: RedisClient,
) -> ConversationService:
    """Dependency to get conversation service."""
    return ConversationService(
        sms_service,
        llm_service,
        user_service,
        crisis_service,
        compliance_service,
        redis_client,
    )
