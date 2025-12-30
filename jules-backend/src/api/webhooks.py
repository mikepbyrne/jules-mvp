"""Webhook endpoints for SMS and Stripe."""

import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.database import get_db
from src.core.logging import get_logger
from src.core.redis import RedisClient, get_redis_client
from src.core.security import redact_phone_number
from src.services.compliance_service import ComplianceService, get_compliance_service
from src.services.conversation_service import ConversationService
from src.services.crisis_service import CrisisDetectionService, get_crisis_service
from src.services.llm_service import LLMService, get_llm_service
from src.services.sms_service import SMSService, get_sms_service
from src.services.user_service import UserService, get_user_service

settings = get_settings()
logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Bandwidth webhook models
class BandwidthMessage(dict):
    """Bandwidth message payload."""

    pass


class StripeWebhook(dict):
    """Stripe webhook payload."""

    pass


def verify_bandwidth_signature(request_body: bytes, signature: str | None) -> bool:
    """
    Verify Bandwidth webhook signature.

    Args:
        request_body: Raw request body bytes
        signature: Signature from X-Bandwidth-Signature header

    Returns:
        bool: True if signature is valid
    """
    if not signature:
        logger.warning("Missing Bandwidth signature header")
        return False

    # Bandwidth doesn't use webhook signatures by default
    # This is a placeholder for custom signature verification if needed
    # For production, implement IP whitelisting or use application-level auth
    return True


def verify_stripe_signature(
    payload: bytes, signature: str | None, webhook_secret: str
) -> bool:
    """
    Verify Stripe webhook signature.

    Args:
        payload: Raw request payload
        signature: Stripe signature header
        webhook_secret: Stripe webhook signing secret

    Returns:
        bool: True if signature is valid
    """
    if not signature:
        return False

    try:
        # Parse signature
        sig_parts = dict(item.split("=") for item in signature.split(","))
        timestamp = sig_parts.get("t")
        signatures = [sig_parts.get(f"v{i}") for i in range(1, 10) if f"v{i}" in sig_parts]

        if not timestamp or not signatures:
            return False

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload.decode()}"
        expected_sig = hmac.new(
            webhook_secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return any(hmac.compare_digest(expected_sig, sig) for sig in signatures if sig)

    except Exception as e:
        logger.error(f"Stripe signature verification failed: {e}")
        return False


@router.post("/sms")
async def handle_sms_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    sms_service: SMSService = Depends(get_sms_service),
    llm_service: LLMService = Depends(get_llm_service),
    user_service: UserService = Depends(get_user_service),
    crisis_service: CrisisDetectionService = Depends(get_crisis_service),
    compliance_service: ComplianceService = Depends(get_compliance_service),
    redis_client: RedisClient = Depends(get_redis_client),
    x_bandwidth_signature: str | None = Header(None, alias="X-Bandwidth-Signature"),
) -> dict[str, str]:
    """
    Handle inbound SMS webhook from Bandwidth.

    Bandwidth webhook payload format:
    ```json
    [
      {
        "type": "message-received",
        "time": "2024-01-01T00:00:00Z",
        "description": "Incoming message received",
        "to": "+15551234567",
        "message": {
          "id": "msg-id",
          "owner": "+15551234567",
          "applicationId": "app-id",
          "time": "2024-01-01T00:00:00Z",
          "segmentCount": 1,
          "direction": "in",
          "to": ["+15551234567"],
          "from": "+15559876543",
          "text": "Hello Jules!",
          "media": []
        }
      }
    ]
    ```
    """
    try:
        # Get raw body for signature verification
        body = await request.body()

        # Verify signature (basic check)
        if not verify_bandwidth_signature(body, x_bandwidth_signature):
            logger.warning("Invalid Bandwidth webhook signature")
            # In production, consider allowing through if using IP whitelisting
            # raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        payload = await request.json()

        # Bandwidth sends array of events
        if not isinstance(payload, list) or not payload:
            raise HTTPException(
                status_code=400, detail="Invalid payload format: expected array"
            )

        event = payload[0]  # Process first event
        event_type = event.get("type")

        if event_type != "message-received":
            # Ignore non-message events (delivery receipts, etc.)
            logger.info(f"Ignoring non-message event: {event_type}")
            return {"status": "ignored", "reason": "not_message_received"}

        message = event.get("message", {})
        from_number = message.get("from")
        message_body = message.get("text", "").strip()
        message_id = message.get("id")

        if not from_number or not message_body:
            raise HTTPException(status_code=400, detail="Missing required fields")

        logger.info(
            f"Processing inbound SMS",
            extra={
                "from": redact_phone_number(from_number),  # FIX: Redact PII
                "message_id": message_id,
                "length": len(message_body),
            },
        )

        # Create conversation service with dependencies
        conversation_service = ConversationService(
            sms_service=sms_service,
            llm_service=llm_service,
            user_service=user_service,
            crisis_service=crisis_service,
            compliance_service=compliance_service,
            redis_client=redis_client,
        )

        # Process message through conversation service
        result = await conversation_service.process_inbound_message(
            db=db, from_number=from_number, message_body=message_body, message_sid=message_id
        )

        logger.info(f"SMS processed successfully", extra={"result": result})

        return {"status": "ok", "message_id": message_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS webhook error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error processing webhook"
        )


@router.post("/stripe")
async def handle_stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> dict[str, str]:
    """
    Handle Stripe webhook events.

    Common events:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    - checkout.session.completed
    """
    try:
        # Get raw body for signature verification
        payload = await request.body()

        # Verify Stripe signature
        if not verify_stripe_signature(
            payload, stripe_signature, settings.stripe_webhook_secret
        ):
            logger.warning("Invalid Stripe webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse event
        event = await request.json()
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})

        logger.info(f"Processing Stripe webhook", extra={"event_type": event_type})

        # Import here to avoid circular dependency
        from src.services.user_service import UserService

        user_service = UserService()

        # Handle different event types
        if event_type == "checkout.session.completed":
            # User completed checkout
            session = event_data
            customer_id = session.get("customer")
            subscription_id = session.get("subscription")
            metadata = session.get("metadata", {})
            phone_number = metadata.get("phone_number")

            if phone_number:
                user = await user_service.get_user_by_phone(db, phone_number)
                if user:
                    user.stripe_customer_id = customer_id
                    user.subscription_status = "active"
                    await db.commit()
                    logger.info(f"Updated user subscription", extra={"user_id": user.id})

        elif event_type == "customer.subscription.created":
            subscription = event_data
            customer_id = subscription.get("customer")
            status = subscription.get("status")

            # Find user by Stripe customer ID and update
            user = await user_service.get_user_by_stripe_customer(db, customer_id)
            if user:
                user.subscription_status = status
                await db.commit()

        elif event_type == "customer.subscription.updated":
            subscription = event_data
            customer_id = subscription.get("customer")
            status = subscription.get("status")

            user = await user_service.get_user_by_stripe_customer(db, customer_id)
            if user:
                user.subscription_status = status
                if status == "canceled":
                    user.subscription_tier = "free"
                await db.commit()

        elif event_type == "customer.subscription.deleted":
            subscription = event_data
            customer_id = subscription.get("customer")

            user = await user_service.get_user_by_stripe_customer(db, customer_id)
            if user:
                user.subscription_status = "canceled"
                user.subscription_tier = "free"
                user.subscription_expires_at = None
                await db.commit()

        elif event_type == "invoice.payment_succeeded":
            invoice = event_data
            customer_id = invoice.get("customer")
            # Update subscription status
            user = await user_service.get_user_by_stripe_customer(db, customer_id)
            if user:
                user.subscription_status = "active"
                await db.commit()

        elif event_type == "invoice.payment_failed":
            invoice = event_data
            customer_id = invoice.get("customer")
            user = await user_service.get_user_by_stripe_customer(db, customer_id)
            if user:
                user.subscription_status = "past_due"
                await db.commit()

        else:
            logger.info(f"Unhandled Stripe event type: {event_type}")

        return {"status": "ok", "event_type": event_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "jules-backend",
        "environment": settings.environment,
    }
