"""
Enhanced SMS delivery with error handling - Drop-in replacement for app_housekeeper.py

This module provides improved send_sms function with:
- Better error handling
- Delivery status tracking
- Retry logic
- Detailed logging
"""
import os
import logging
from typing import Dict, Optional
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

# Twilio setup
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms(to: str, body: str, retry_count: int = 0, max_retries: int = 0) -> Dict:
    """
    Send SMS via Twilio with enhanced error handling.

    Args:
        to: Recipient phone number (E.164 format)
        body: Message body text
        retry_count: Current retry attempt (internal use)
        max_retries: Maximum retry attempts (0 = no retries)

    Returns:
        Dict with:
            - success: bool
            - message_sid: str (if successful)
            - status: str (if successful)
            - error: str (if failed)
            - error_code: int (if Twilio error)
            - error_type: str (if failed)
    """
    try:
        message = twilio_client.messages.create(
            to=to,
            from_=TWILIO_PHONE,
            body=body
        )

        logger.info(
            f"sms_sent to={to} sid={message.sid} status={message.status} "
            f"segments={message.num_segments} price={message.price}"
        )

        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status,
            "num_segments": message.num_segments,
            "price": message.price
        }

    except TwilioRestException as e:
        error_code = e.code
        error_msg = e.msg

        logger.error(
            f"sms_failed to={to} error_code={error_code} error={error_msg} "
            f"retry_count={retry_count}",
            exc_info=True
        )

        # Check if error is retryable
        retryable_errors = {
            20003,  # Authentication error - not retryable but log
            21211,  # Invalid phone number
            21408,  # Account doesn't have permission
            21610,  # Phone number is blacklisted
            30001,  # Queue overflow
            30003,  # Unreachable destination
            30005,  # Unknown destination
            30006,  # Landline or unreachable carrier
            30007,  # Carrier violation
            30008,  # Unknown error
        }

        # Error 30032 is NOT retryable - account/number issue
        if error_code == 30032:
            return {
                "success": False,
                "error": "Account suspended or toll-free verification required",
                "error_code": error_code,
                "error_type": "TwilioRestException",
                "retryable": False,
                "help": "Check toll-free verification status or account billing"
            }

        # Retry logic for transient errors
        if error_code in retryable_errors and retry_count < max_retries:
            import time
            wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30s
            logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{max_retries})")
            time.sleep(wait_time)
            return send_sms(to, body, retry_count + 1, max_retries)

        return {
            "success": False,
            "error": error_msg,
            "error_code": error_code,
            "error_type": "TwilioRestException",
            "retryable": error_code in retryable_errors
        }

    except Exception as e:
        logger.error(f"sms_failed to={to} error={str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "retryable": False
        }


def check_message_status(message_sid: str) -> Dict:
    """
    Check the delivery status of a sent message.

    Args:
        message_sid: Twilio message SID

    Returns:
        Dict with message status details
    """
    try:
        message = twilio_client.messages(message_sid).fetch()

        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status,
            "error_code": message.error_code,
            "error_message": message.error_message,
            "date_sent": message.date_sent.isoformat() if message.date_sent else None,
            "date_updated": message.date_updated.isoformat() if message.date_updated else None,
            "price": message.price,
            "price_unit": message.price_unit
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# FastAPI endpoint for status callbacks (add to app_housekeeper.py)
"""
@app.post("/sms/status")
async def sms_status_callback(
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    To: str = Form(...),
    ErrorCode: Optional[str] = Form(None),
    ErrorMessage: Optional[str] = Form(None)
):
    Handle message delivery status updates from Twilio.

    logger.info(
        f"sms_status_update sid={MessageSid} to={To} "
        f"status={MessageStatus} error_code={ErrorCode}"
    )

    # Handle delivery failures
    if MessageStatus in ['undelivered', 'failed']:
        logger.error(
            f"Message delivery failed: sid={MessageSid} "
            f"error={ErrorCode} - {ErrorMessage}"
        )

        # Could implement:
        # - Store failed message in queue for retry
        # - Alert admin
        # - Update user state to indicate message failed
        # - Send alternative notification (email, push, etc.)

    elif MessageStatus == 'delivered':
        logger.info(f"Message delivered successfully: sid={MessageSid}")

    return PlainTextResponse(
        '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    )
"""


if __name__ == '__main__':
    # Test the enhanced SMS sending
    import sys

    if len(sys.argv) < 3:
        print("Usage: python sms_delivery_fix.py <to_number> <message>")
        sys.exit(1)

    to_number = sys.argv[1]
    message_text = sys.argv[2]

    print(f"Sending test message to {to_number}...")
    result = send_sms(to_number, message_text)

    print("\nResult:")
    import json
    print(json.dumps(result, indent=2))

    if result["success"]:
        print("\nChecking delivery status...")
        import time
        time.sleep(2)  # Wait a moment for status update

        status = check_message_status(result["message_sid"])
        print("\nStatus:")
        print(json.dumps(status, indent=2))
