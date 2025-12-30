"""Stripe payment and subscription service."""

import asyncio
from functools import partial
from typing import Any

import stripe

from src.config import get_settings
from src.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """
    Service for handling Stripe payments and subscriptions.

    Manages customer creation, subscription management, and payment processing.

    Note: Stripe Python SDK v8.2.0 uses synchronous HTTP calls. All methods wrap
    synchronous Stripe API calls in asyncio.run_in_executor() to make them non-blocking.
    """

    def __init__(self) -> None:
        """Initialize Stripe service."""
        self.price_id_monthly = settings.stripe_price_id_monthly
        self.price_id_annual = settings.stripe_price_id_annual

    async def create_customer(
        self, phone_number: str, email: str | None = None, metadata: dict[str, Any] | None = None
    ) -> stripe.Customer:
        """
        Create a new Stripe customer.

        Args:
            phone_number: Customer phone number
            email: Customer email (optional)
            metadata: Additional metadata

        Returns:
            stripe.Customer: Created customer object
        """
        try:
            customer_data = {
                "phone": phone_number,
                "metadata": metadata or {},
            }

            if email:
                customer_data["email"] = email

            loop = asyncio.get_event_loop()
            customer = await loop.run_in_executor(
                None,
                partial(stripe.Customer.create, **customer_data)
            )

            logger.info(
                f"Stripe customer created",
                extra={"customer_id": customer.id, "phone": phone_number[:6] + "***"},
            )

            return customer

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to create Stripe customer",
                extra={"error": str(e), "phone": phone_number[:6] + "***"},
                exc_info=True,
            )
            raise

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> stripe.checkout.Session:
        """
        Create a Stripe Checkout session for subscription.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            metadata: Additional metadata

        Returns:
            stripe.checkout.Session: Created session
        """
        try:
            loop = asyncio.get_event_loop()
            session = await loop.run_in_executor(
                None,
                partial(
                    stripe.checkout.Session.create,
                    customer=customer_id,
                    payment_method_types=["card"],
                    line_items=[{"price": price_id, "quantity": 1}],
                    mode="subscription",
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata=metadata or {},
                    subscription_data={
                        "metadata": metadata or {},
                    },
                )
            )

            logger.info(
                f"Checkout session created",
                extra={"session_id": session.id, "customer_id": customer_id},
            )

            return session

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to create checkout session",
                extra={"error": str(e), "customer_id": customer_id},
                exc_info=True,
            )
            raise

    async def create_billing_portal_session(
        self, customer_id: str, return_url: str
    ) -> stripe.billing_portal.Session:
        """
        Create a billing portal session for customer to manage subscription.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session

        Returns:
            stripe.billing_portal.Session: Portal session
        """
        try:
            loop = asyncio.get_event_loop()
            session = await loop.run_in_executor(
                None,
                partial(
                    stripe.billing_portal.Session.create,
                    customer=customer_id,
                    return_url=return_url
                )
            )

            logger.info(
                f"Billing portal session created",
                extra={"session_id": session.id, "customer_id": customer_id},
            )

            return session

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to create billing portal session",
                extra={"error": str(e), "customer_id": customer_id},
                exc_info=True,
            )
            raise

    async def get_subscription(self, subscription_id: str) -> stripe.Subscription:
        """
        Retrieve a subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            stripe.Subscription: Subscription object
        """
        try:
            loop = asyncio.get_event_loop()
            subscription = await loop.run_in_executor(
                None,
                partial(stripe.Subscription.retrieve, subscription_id)
            )
            return subscription

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to retrieve subscription",
                extra={"error": str(e), "subscription_id": subscription_id},
                exc_info=True,
            )
            raise

    async def cancel_subscription(
        self, subscription_id: str, cancel_at_period_end: bool = True
    ) -> stripe.Subscription:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            cancel_at_period_end: If True, cancel at end of billing period

        Returns:
            stripe.Subscription: Updated subscription
        """
        try:
            loop = asyncio.get_event_loop()

            if cancel_at_period_end:
                subscription = await loop.run_in_executor(
                    None,
                    partial(
                        stripe.Subscription.modify,
                        subscription_id,
                        cancel_at_period_end=True
                    )
                )
            else:
                subscription = await loop.run_in_executor(
                    None,
                    partial(stripe.Subscription.delete, subscription_id)
                )

            logger.info(
                f"Subscription canceled",
                extra={
                    "subscription_id": subscription_id,
                    "cancel_at_period_end": cancel_at_period_end,
                },
            )

            return subscription

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to cancel subscription",
                extra={"error": str(e), "subscription_id": subscription_id},
                exc_info=True,
            )
            raise

    async def update_subscription(
        self, subscription_id: str, price_id: str
    ) -> stripe.Subscription:
        """
        Update subscription to a new price/plan.

        Args:
            subscription_id: Stripe subscription ID
            price_id: New price ID

        Returns:
            stripe.Subscription: Updated subscription
        """
        try:
            loop = asyncio.get_event_loop()

            # Get current subscription
            subscription = await loop.run_in_executor(
                None,
                partial(stripe.Subscription.retrieve, subscription_id)
            )

            # Update to new price
            subscription = await loop.run_in_executor(
                None,
                partial(
                    stripe.Subscription.modify,
                    subscription_id,
                    items=[
                        {
                            "id": subscription["items"]["data"][0].id,
                            "price": price_id,
                        }
                    ],
                )
            )

            logger.info(
                f"Subscription updated",
                extra={"subscription_id": subscription_id, "new_price_id": price_id},
            )

            return subscription

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to update subscription",
                extra={"error": str(e), "subscription_id": subscription_id},
                exc_info=True,
            )
            raise

    async def get_customer(self, customer_id: str) -> stripe.Customer:
        """
        Retrieve customer details.

        Args:
            customer_id: Stripe customer ID

        Returns:
            stripe.Customer: Customer object
        """
        try:
            loop = asyncio.get_event_loop()
            customer = await loop.run_in_executor(
                None,
                partial(stripe.Customer.retrieve, customer_id)
            )
            return customer

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to retrieve customer",
                extra={"error": str(e), "customer_id": customer_id},
                exc_info=True,
            )
            raise

    async def list_customer_subscriptions(
        self, customer_id: str
    ) -> list[stripe.Subscription]:
        """
        List all subscriptions for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            list[stripe.Subscription]: List of subscriptions
        """
        try:
            loop = asyncio.get_event_loop()
            subscriptions = await loop.run_in_executor(
                None,
                partial(stripe.Subscription.list, customer=customer_id, limit=10)
            )
            return subscriptions.data

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to list subscriptions",
                extra={"error": str(e), "customer_id": customer_id},
                exc_info=True,
            )
            raise

    def get_price_info(self, tier: str) -> dict[str, Any]:
        """
        Get price information for a subscription tier.

        Args:
            tier: Subscription tier (monthly or annual)

        Returns:
            dict: Price information
        """
        if tier == "monthly":
            return {
                "price_id": self.price_id_monthly,
                "tier": "monthly",
                "display_name": "Monthly Subscription",
                "interval": "month",
            }
        elif tier == "annual":
            return {
                "price_id": self.price_id_annual,
                "tier": "annual",
                "display_name": "Annual Subscription",
                "interval": "year",
            }
        else:
            raise ValueError(f"Invalid subscription tier: {tier}")

    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> stripe.PaymentIntent:
        """
        Create a payment intent for one-time payment.

        Args:
            amount: Amount in cents
            currency: Currency code (default: usd)
            customer_id: Stripe customer ID (optional)
            metadata: Additional metadata

        Returns:
            stripe.PaymentIntent: Created payment intent
        """
        try:
            intent_data = {
                "amount": amount,
                "currency": currency,
                "metadata": metadata or {},
            }

            if customer_id:
                intent_data["customer"] = customer_id

            loop = asyncio.get_event_loop()
            intent = await loop.run_in_executor(
                None,
                partial(stripe.PaymentIntent.create, **intent_data)
            )

            logger.info(
                f"Payment intent created",
                extra={"intent_id": intent.id, "amount": amount, "currency": currency},
            )

            return intent

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to create payment intent",
                extra={"error": str(e), "amount": amount},
                exc_info=True,
            )
            raise


# Global Stripe service instance
stripe_service = StripeService()


async def get_stripe_service() -> StripeService:
    """Dependency to get Stripe service."""
    return stripe_service
