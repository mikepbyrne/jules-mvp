"""
Twilio webhook handler with signature verification.

Validates all incoming webhooks to prevent forgery.
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from twilio.request_validator import RequestValidator
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_twilio_validator() -> RequestValidator:
    """Get Twilio request validator."""
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not auth_token:
        raise ValueError("TWILIO_AUTH_TOKEN environment variable required")

    return RequestValidator(auth_token)


async def verify_twilio_signature(
    request: Request,
    validator: RequestValidator = Depends(get_twilio_validator)
) -> bool:
    """
    Verify Twilio webhook signature.

    Prevents forged webhooks from attackers.
    """
    # Get signature from header
    signature = request.headers.get("X-Twilio-Signature")

    if not signature:
        logger.warning("webhook_missing_signature",
                      path=request.url.path,
                      client=request.client.host if request.client else None)
        raise HTTPException(status_code=403, detail="Missing Twilio signature")

    # Get request URL
    url = str(request.url)

    # Get form parameters
    form_data = await request.form()
    params = dict(form_data)

    # Validate signature
    is_valid = validator.validate(url, params, signature)

    if not is_valid:
        logger.error("webhook_invalid_signature",
                    path=request.url.path,
                    client=request.client.host if request.client else None)
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    logger.info("webhook_verified", path=request.url.path)

    return True


@router.post("/sms/webhook")
async def sms_webhook(
    request: Request,
    verified: bool = Depends(verify_twilio_signature)
):
    """
    Handle inbound SMS webhook from Twilio.

    Signature is verified by dependency injection.
    """
    form_data = await request.form()
    params = dict(form_data)

    from_number = params.get("From")
    body = params.get("Body")
    media_url = params.get("MediaUrl0")  # First media attachment
    message_sid = params.get("MessageSid")

    logger.info("sms_received",
               from_number=from_number,
               message_sid=message_sid,
               has_media=bool(media_url))

    # Route to message processor
    from backend.services.sms.message_processor import process_inbound_message

    try:
        response = await process_inbound_message(
            from_number=from_number,
            body=body,
            media_url=media_url,
            message_sid=message_sid
        )

        return {"status": "processed", "response": response}

    except Exception as e:
        logger.error("sms_processing_failed",
                    message_sid=message_sid,
                    error=str(e))

        # Still return 200 to Twilio to prevent retries
        return {"status": "error", "message": "Processing failed"}


@router.post("/sms/status")
async def sms_status_callback(
    request: Request,
    verified: bool = Depends(verify_twilio_signature)
):
    """
    Handle SMS delivery status callback from Twilio.

    Tracks message delivery success/failure.
    """
    form_data = await request.form()
    params = dict(form_data)

    message_sid = params.get("MessageSid")
    message_status = params.get("MessageStatus")
    error_code = params.get("ErrorCode")

    logger.info("sms_status_update",
               message_sid=message_sid,
               status=message_status,
               error_code=error_code)

    # Update message delivery status in database
    from backend.services.sms.delivery_tracker import update_delivery_status

    await update_delivery_status(
        message_sid=message_sid,
        status=message_status,
        error_code=error_code
    )

    return {"status": "received"}
