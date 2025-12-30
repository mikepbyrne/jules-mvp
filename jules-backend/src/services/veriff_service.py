"""Veriff age verification service."""

import hashlib
import hmac
import time
import uuid
from datetime import datetime
from typing import Any

import httpx

from src.config import get_settings
from src.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class VeriffService:
    """
    Service for age verification using Veriff API.

    Veriff provides identity and age verification through document upload
    and facial recognition.
    """

    def __init__(self) -> None:
        """Initialize Veriff service."""
        self.api_key = settings.veriff_api_key
        self.api_secret = settings.veriff_api_secret
        self.base_url = str(settings.veriff_base_url)

    def _generate_signature(self, payload: bytes) -> str:
        """
        Generate HMAC signature for Veriff API request.

        Args:
            payload: Request payload as bytes

        Returns:
            str: Hex-encoded HMAC signature
        """
        signature = hmac.new(
            self.api_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        return signature.lower()

    async def create_verification_session(
        self, user_id: int, phone_number: str
    ) -> dict[str, Any]:
        """
        Create a new Veriff verification session.

        Args:
            user_id: Internal user ID
            phone_number: User's phone number

        Returns:
            dict: Session details including verification URL

        Response format:
        {
            "status": "success",
            "verification": {
                "id": "uuid",
                "url": "https://...",
                "vendorData": "user_123",
                "host": "https://...",
                "status": "created"
            }
        }
        """
        session_id = str(uuid.uuid4())

        payload = {
            "verification": {
                "callback": f"{self.base_url}/api/webhooks/veriff",
                "person": {
                    "firstName": "User",  # Will be updated during verification
                    "lastName": str(user_id),  # Use user_id temporarily
                },
                "vendorData": str(user_id),  # Reference to our user
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                # Serialize payload
                import json

                payload_bytes = json.dumps(payload).encode()

                # Generate signature
                signature = self._generate_signature(payload_bytes)

                # Make request
                response = await client.post(
                    f"{self.base_url}/v1/sessions",
                    content=payload_bytes,
                    headers={
                        "Content-Type": "application/json",
                        "X-AUTH-CLIENT": self.api_key,
                        "X-SIGNATURE": signature,
                    },
                    timeout=30.0,
                )

                response.raise_for_status()
                result = response.json()

                logger.info(
                    f"Veriff session created",
                    extra={
                        "user_id": user_id,
                        "session_id": result.get("verification", {}).get("id"),
                    },
                )

                return result

            except httpx.HTTPError as e:
                logger.error(
                    f"Failed to create Veriff session",
                    extra={"user_id": user_id, "error": str(e)},
                    exc_info=True,
                )
                raise

    async def get_verification_decision(self, session_id: str) -> dict[str, Any]:
        """
        Get verification decision for a session.

        Args:
            session_id: Veriff session ID

        Returns:
            dict: Verification decision

        Response format:
        {
            "status": "success",
            "verification": {
                "id": "uuid",
                "code": 9001,
                "person": {
                    "firstName": "John",
                    "lastName": "Doe",
                    "dateOfBirth": "1990-01-01"
                },
                "status": "approved",
                "vendorData": "user_123"
            }
        }
        """
        async with httpx.AsyncClient() as client:
            try:
                # Make request
                timestamp = str(int(time.time()))
                signature_payload = f"{session_id}{timestamp}".encode()
                signature = self._generate_signature(signature_payload)

                response = await client.get(
                    f"{self.base_url}/v1/sessions/{session_id}/decision",
                    headers={
                        "X-AUTH-CLIENT": self.api_key,
                        "X-HMAC-SIGNATURE": signature,
                    },
                    timeout=30.0,
                )

                response.raise_for_status()
                result = response.json()

                logger.info(
                    f"Retrieved Veriff decision",
                    extra={
                        "session_id": session_id,
                        "status": result.get("verification", {}).get("status"),
                    },
                )

                return result

            except httpx.HTTPError as e:
                logger.error(
                    f"Failed to get Veriff decision",
                    extra={"session_id": session_id, "error": str(e)},
                    exc_info=True,
                )
                raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Veriff webhook signature.

        Args:
            payload: Raw webhook payload
            signature: X-SIGNATURE header value

        Returns:
            bool: True if signature is valid
        """
        expected_signature = self._generate_signature(payload)
        return hmac.compare_digest(expected_signature, signature.lower())

    def parse_verification_result(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """
        Parse Veriff verification webhook result.

        Args:
            webhook_data: Webhook payload from Veriff

        Returns:
            dict: Parsed verification result

        Example webhook:
        {
            "id": "uuid",
            "feature": "verification",
            "code": 9001,
            "action": "completed",
            "vendorData": "user_123",
            "decisionTime": "2024-01-01T00:00:00Z",
            "acceptanceTime": "2024-01-01T00:00:00Z",
            "verification": {
                "status": "approved",
                "person": {
                    "firstName": "John",
                    "lastName": "Doe",
                    "dateOfBirth": "1990-01-01"
                }
            }
        }
        """
        verification = webhook_data.get("verification", {})
        person = verification.get("person", {})
        status = verification.get("status")
        code = webhook_data.get("code")

        # Parse date of birth
        dob_str = person.get("dateOfBirth")
        age = None
        is_minor = False

        if dob_str:
            try:
                from dateutil import parser

                dob = parser.parse(dob_str)
                today = datetime.utcnow()
                age = (
                    today.year
                    - dob.year
                    - ((today.month, today.day) < (dob.month, dob.day))
                )
                is_minor = age < 18
            except Exception as e:
                logger.error(f"Failed to parse date of birth: {e}")

        return {
            "user_id": int(webhook_data.get("vendorData", 0)),
            "session_id": webhook_data.get("id"),
            "status": status,
            "code": code,
            "approved": status == "approved" and code == 9001,
            "age": age,
            "is_minor": is_minor,
            "first_name": person.get("firstName"),
            "last_name": person.get("lastName"),
            "date_of_birth": dob_str,
            "decision_time": webhook_data.get("decisionTime"),
        }

    async def send_verification_sms(self, phone_number: str, session_url: str) -> None:
        """
        Send verification link via SMS.

        This would typically be sent through the SMS service.

        Args:
            phone_number: User's phone number
            session_url: Veriff session URL
        """
        from src.services.sms_service import sms_service

        message = (
            f"Please verify your age to continue using Jules:\n\n"
            f"{session_url}\n\n"
            f"This is required for compliance. The process takes ~2 minutes."
        )

        await sms_service.send_message(phone_number, message)

        logger.info(
            f"Verification SMS sent",
            extra={"phone_number": phone_number[:6] + "***"},
        )


# Global Veriff service instance
veriff_service = VeriffService()


async def get_veriff_service() -> VeriffService:
    """Dependency to get Veriff service."""
    return veriff_service
