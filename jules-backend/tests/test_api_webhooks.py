"""Tests for API webhook endpoints."""

import json

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestWebhookEndpoints:
    """Test suite for webhook endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/webhooks/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "jules-backend"

    async def test_sms_webhook_valid(
        self,
        client: AsyncClient,
        mocker,
    ):
        """Test valid SMS webhook."""
        # Mock the conversation service
        mock_process = mocker.patch(
            "src.api.webhooks.ConversationService.process_inbound_message",
            return_value={
                "status": "success",
                "user_id": 1,
                "conversation_id": 1,
            },
        )

        # Bandwidth webhook payload
        payload = [
            {
                "type": "message-received",
                "time": "2024-01-01T00:00:00Z",
                "description": "Incoming message",
                "to": "+15551234567",
                "message": {
                    "id": "msg-test-123",
                    "owner": "+15551234567",
                    "applicationId": "app-123",
                    "time": "2024-01-01T00:00:00Z",
                    "segmentCount": 1,
                    "direction": "in",
                    "to": ["+15551234567"],
                    "from": "+15559876543",
                    "text": "Hello Jules!",
                    "media": [],
                },
            }
        ]

        response = await client.post("/webhooks/sms", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["message_id"] == "msg-test-123"

    async def test_sms_webhook_non_message_event(self, client: AsyncClient):
        """Test SMS webhook with non-message event (e.g., delivery receipt)."""
        payload = [
            {
                "type": "message-delivered",
                "time": "2024-01-01T00:00:00Z",
                "description": "Message delivered",
                "message": {"id": "msg-123"},
            }
        ]

        response = await client.post("/webhooks/sms", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"

    async def test_sms_webhook_invalid_payload(self, client: AsyncClient):
        """Test SMS webhook with invalid payload."""
        # Empty array
        response = await client.post("/webhooks/sms", json=[])
        assert response.status_code == 400

        # Not an array
        response = await client.post("/webhooks/sms", json={"invalid": "payload"})
        assert response.status_code == 400

    async def test_sms_webhook_missing_fields(self, client: AsyncClient):
        """Test SMS webhook with missing required fields."""
        payload = [
            {
                "type": "message-received",
                "message": {
                    "id": "msg-123",
                    # Missing 'from' and 'text'
                },
            }
        ]

        response = await client.post("/webhooks/sms", json=payload)
        assert response.status_code == 400

    async def test_stripe_webhook_checkout_completed(
        self,
        client: AsyncClient,
        user_factory,
        db_session,
        mocker,
    ):
        """Test Stripe checkout.session.completed webhook."""
        # Create test user
        user = await user_factory(phone_number="+15551234567")

        # Mock Stripe signature verification
        mocker.patch(
            "src.api.webhooks.verify_stripe_signature",
            return_value=True,
        )

        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "metadata": {"phone_number": "+15551234567"},
                }
            },
        }

        response = await client.post(
            "/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": "valid-signature"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["event_type"] == "checkout.session.completed"

        # Verify user was updated
        await db_session.refresh(user)
        assert user.stripe_customer_id == "cus_test_123"
        assert user.subscription_status == "active"

    async def test_stripe_webhook_subscription_updated(
        self,
        client: AsyncClient,
        user_factory,
        db_session,
        mocker,
    ):
        """Test Stripe subscription.updated webhook."""
        user = await user_factory(
            phone_number="+15551234567",
            stripe_customer_id="cus_test_123",
        )

        mocker.patch(
            "src.api.webhooks.verify_stripe_signature",
            return_value=True,
        )

        payload = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "active",
                }
            },
        }

        response = await client.post(
            "/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": "valid-signature"},
        )

        assert response.status_code == 200

        await db_session.refresh(user)
        assert user.subscription_status == "active"

    async def test_stripe_webhook_subscription_canceled(
        self,
        client: AsyncClient,
        user_factory,
        db_session,
        mocker,
    ):
        """Test Stripe subscription.deleted webhook."""
        user = await user_factory(
            phone_number="+15551234567",
            stripe_customer_id="cus_test_123",
            subscription_tier="monthly",
        )

        mocker.patch(
            "src.api.webhooks.verify_stripe_signature",
            return_value=True,
        )

        payload = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                }
            },
        }

        response = await client.post(
            "/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": "valid-signature"},
        )

        assert response.status_code == 200

        await db_session.refresh(user)
        assert user.subscription_status == "canceled"
        assert user.subscription_tier == "free"

    async def test_stripe_webhook_invalid_signature(self, client: AsyncClient, mocker):
        """Test Stripe webhook with invalid signature."""
        mocker.patch(
            "src.api.webhooks.verify_stripe_signature",
            return_value=False,
        )

        payload = {"type": "test.event"}

        response = await client.post(
            "/webhooks/stripe",
            json=payload,
            headers={"Stripe-Signature": "invalid"},
        )

        assert response.status_code == 401

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root API endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Jules Backend API"
        assert "version" in data
        assert "environment" in data

    async def test_health_check_detailed(self, client: AsyncClient):
        """Test detailed health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]


@pytest.mark.asyncio
class TestStripeSignatureVerification:
    """Test Stripe signature verification."""

    def test_verify_stripe_signature_valid(self):
        """Test valid Stripe signature."""
        from src.api.webhooks import verify_stripe_signature
        import time
        import hmac
        import hashlib

        webhook_secret = "whsec_test_secret"
        payload = b'{"test": "data"}'
        timestamp = str(int(time.time()))

        # Generate valid signature
        signed_payload = f"{timestamp}.{payload.decode()}"
        signature = hmac.new(
            webhook_secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()

        header = f"t={timestamp},v1={signature}"

        result = verify_stripe_signature(payload, header, webhook_secret)
        assert result is True

    def test_verify_stripe_signature_invalid(self):
        """Test invalid Stripe signature."""
        from src.api.webhooks import verify_stripe_signature

        result = verify_stripe_signature(
            b'{"test": "data"}', "t=123,v1=invalid", "whsec_test_secret"
        )
        assert result is False

    def test_verify_stripe_signature_missing(self):
        """Test missing signature."""
        from src.api.webhooks import verify_stripe_signature

        result = verify_stripe_signature(b'{"test": "data"}', None, "whsec_test_secret")
        assert result is False
