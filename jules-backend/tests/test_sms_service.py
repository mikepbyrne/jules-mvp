"""Tests for SMS service."""

import pytest
from httpx import AsyncClient, Response

from src.services.sms_service import SMSService


@pytest.mark.asyncio
class TestSMSService:
    """Test suite for SMS service."""

    async def test_send_message_success(self, mocker):
        """Test successful message sending."""
        # Mock HTTP response
        mock_response = mocker.Mock(spec=Response)
        mock_response.json.return_value = {
            "id": "msg-test-123",
            "time": "2024-01-01T00:00:00Z",
            "status": "sent",
        }
        mock_response.raise_for_status = mocker.Mock()

        # Mock AsyncClient
        mock_client = mocker.AsyncMock(spec=AsyncClient)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        # Test
        service = SMSService()
        result = await service.send_message("+15551234567", "Test message")

        assert result["id"] == "msg-test-123"
        assert result["status"] == "sent"

        # Verify API call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "+15551234567" in str(call_args)
        assert "Test message" in str(call_args)

    async def test_send_message_failure(self, mocker):
        """Test message sending failure."""
        from httpx import HTTPError

        # Mock failed response
        mock_client = mocker.AsyncMock(spec=AsyncClient)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.side_effect = HTTPError("API error")

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        # Test
        service = SMSService()
        with pytest.raises(HTTPError):
            await service.send_message("+15551234567", "Test message")

    def test_validate_phone_number(self):
        """Test phone number validation."""
        service = SMSService()

        # Valid 10-digit number
        assert service.validate_phone_number("5551234567") == "+15551234567"
        assert service.validate_phone_number("555-123-4567") == "+15551234567"
        assert service.validate_phone_number("(555) 123-4567") == "+15551234567"

        # Already has +1
        assert service.validate_phone_number("+15551234567") == "+15551234567"
        assert service.validate_phone_number("15551234567") == "+15551234567"

        # Invalid numbers
        with pytest.raises(ValueError):
            service.validate_phone_number("123")
        with pytest.raises(ValueError):
            service.validate_phone_number("55512345")

    async def test_send_mms_success(self, mocker):
        """Test successful MMS sending."""
        mock_response = mocker.Mock(spec=Response)
        mock_response.json.return_value = {
            "id": "msg-mms-123",
            "status": "sent",
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.AsyncMock(spec=AsyncClient)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        service = SMSService()
        result = await service.send_mms(
            "+15551234567", "Check this out", ["https://example.com/image.jpg"]
        )

        assert result["id"] == "msg-mms-123"
        mock_client.post.assert_called_once()

    async def test_get_message_status(self, mocker):
        """Test getting message status."""
        mock_response = mocker.Mock(spec=Response)
        mock_response.json.return_value = {
            "id": "msg-123",
            "status": "delivered",
            "deliveryState": "delivered",
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_client = mocker.AsyncMock(spec=AsyncClient)
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response

        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        service = SMSService()
        result = await service.get_message_status("msg-123")

        assert result["id"] == "msg-123"
        assert result["status"] == "delivered"
