"""SMS service using Bandwidth API."""

import logging
from typing import Any

import httpx

from src.config import get_settings
from src.core.logging import get_logger
from src.core.security import redact_phone_number

settings = get_settings()
logger = get_logger(__name__)


class SMSService:
    """SMS service for sending and receiving messages via Bandwidth."""

    def __init__(self) -> None:
        """Initialize SMS service."""
        self.base_url = "https://messaging.bandwidth.com/api/v2"
        self.account_id = settings.bandwidth_account_id
        self.username = settings.bandwidth_username
        self.password = settings.bandwidth_password
        self.application_id = settings.bandwidth_application_id
        self.from_number = settings.bandwidth_phone_number

    async def send_message(self, to_number: str, message: str) -> dict[str, Any]:
        """
        Send SMS message to a phone number.

        Args:
            to_number: Recipient phone number (E.164 format)
            message: Message content (max 2048 characters for SMS)

        Returns:
            dict: Response from Bandwidth API with message ID

        Raises:
            httpx.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/users/{self.account_id}/messages"

        payload = {
            "from": self.from_number,
            "to": [to_number],
            "text": message,
            "applicationId": self.application_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    auth=(self.username, self.password),
                    timeout=10.0,
                )
                response.raise_for_status()
                result = response.json()

                logger.info(
                    f"SMS sent successfully",
                    extra={
                        "to": redact_phone_number(to_number),  # FIX: Redact PII
                        "message_id": result.get("id"),
                        "status": "sent",
                    },
                )

                return result

            except httpx.HTTPError as e:
                logger.error(
                    f"Failed to send SMS",
                    extra={"to": redact_phone_number(to_number), "error": str(e)},  # FIX: Redact PII
                    exc_info=True,
                )
                raise

    async def send_mms(
        self, to_number: str, message: str, media_urls: list[str]
    ) -> dict[str, Any]:
        """
        Send MMS message with media attachments.

        Args:
            to_number: Recipient phone number
            message: Message content
            media_urls: List of media URLs (images, etc.)

        Returns:
            dict: Response from Bandwidth API
        """
        url = f"{self.base_url}/users/{self.account_id}/messages"

        payload = {
            "from": self.from_number,
            "to": [to_number],
            "text": message,
            "applicationId": self.application_id,
            "media": media_urls,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    auth=(self.username, self.password),
                    timeout=10.0,
                )
                response.raise_for_status()
                result = response.json()

                logger.info(
                    f"MMS sent successfully",
                    extra={
                        "to": to_number,
                        "message_id": result.get("id"),
                        "media_count": len(media_urls),
                    },
                )

                return result

            except httpx.HTTPError as e:
                logger.error(
                    f"Failed to send MMS",
                    extra={"to": to_number, "error": str(e)},
                    exc_info=True,
                )
                raise

    def validate_phone_number(self, phone_number: str) -> str:
        """
        Validate and format phone number to E.164 format.

        Args:
            phone_number: Phone number to validate

        Returns:
            str: Formatted phone number

        Raises:
            ValueError: If phone number is invalid
        """
        # Remove non-numeric characters
        cleaned = "".join(filter(str.isdigit, phone_number))

        # Add +1 for US numbers if not present
        if len(cleaned) == 10:
            cleaned = "1" + cleaned

        if len(cleaned) != 11 or not cleaned.startswith("1"):
            raise ValueError(f"Invalid US phone number: {phone_number}")

        return f"+{cleaned}"

    async def get_message_status(self, message_id: str) -> dict[str, Any]:
        """
        Get the status of a sent message.

        Args:
            message_id: Bandwidth message ID

        Returns:
            dict: Message status information
        """
        url = f"{self.base_url}/users/{self.account_id}/messages/{message_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=(self.username, self.password),
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()


# Global SMS service instance
sms_service = SMSService()


async def get_sms_service() -> SMSService:
    """Dependency to get SMS service."""
    return sms_service
