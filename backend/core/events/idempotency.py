"""
Event idempotency handling.

Prevents duplicate event processing from retries.
"""
from typing import Any, Dict
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event with idempotency key."""
    id: str  # Unique event ID (idempotency key)
    type: str  # Event type (e.g., 'recipe.extracted', 'sms.received')
    data: Dict[str, Any]
    correlation_id: str = None


class IdempotentEventBus:
    """Event bus with duplicate detection."""

    def __init__(self, redis_client, ttl: int = 86400):
        self.redis = redis_client
        self.ttl = ttl  # 24 hours

    async def emit(self, event: Event) -> bool:
        """
        Emit event with idempotency check.

        Returns True if emitted, False if duplicate.
        """
        idempotency_key = f"event:{event.id}"

        # Check if already processed
        exists = await self.redis.exists(idempotency_key)

        if exists:
            logger.warning("duplicate_event",
                          event_id=event.id,
                          event_type=event.type,
                          correlation_id=event.correlation_id)
            return False

        # Emit event to queue
        queue_key = f"events:{event.type}"
        await self.redis.lpush(queue_key, event.json())

        # Mark as processed
        await self.redis.setex(idempotency_key, self.ttl, "1")

        logger.info("event_emitted",
                   event_id=event.id,
                   event_type=event.type,
                   correlation_id=event.correlation_id)

        return True

    async def consume(self, event_type: str, timeout: int = 5) -> Event:
        """
        Consume event from queue (blocking).

        Returns None if timeout reached.
        """
        queue_key = f"events:{event_type}"

        # Blocking pop with timeout
        result = await self.redis.brpop(queue_key, timeout=timeout)

        if not result:
            return None

        _, event_json = result
        event_data = json.loads(event_json)

        return Event(**event_data)

    def json(self) -> str:
        """Serialize event to JSON."""
        return json.dumps({
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "correlation_id": self.correlation_id
        })


# Extend Event class
Event.json = IdempotentEventBus.json
