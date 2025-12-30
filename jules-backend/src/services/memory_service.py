"""Memory and context service for conversation management."""

import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.redis import RedisClient, get_redis_client
from src.core.security import decrypt_data, encrypt_data
from src.models.conversation import Message
from src.models.user import User

logger = get_logger(__name__)


class MemoryService:
    """
    Service for managing conversation memory and user context.

    Handles:
    - Short-term memory (recent messages via Redis)
    - Long-term memory (conversation history via database)
    - User preferences and context
    - Conversation summaries
    """

    def __init__(self, redis_client: RedisClient) -> None:
        """Initialize memory service."""
        self.redis = redis_client
        self.short_term_ttl = 3600  # 1 hour
        self.context_window = 10  # Number of recent messages

    async def get_conversation_context(
        self, db: AsyncSession, user_id: int, conversation_id: int
    ) -> dict[str, Any]:
        """
        Get full conversation context including messages and preferences.

        Args:
            db: Database session
            user_id: User ID
            conversation_id: Conversation ID

        Returns:
            dict: Conversation context with messages, preferences, and metadata
        """
        # Try to get from cache first
        cache_key = f"context:user:{user_id}:conv:{conversation_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                logger.warning(f"Invalid cached context for {cache_key}")

        # Build context from database
        context = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": await self._get_recent_messages(db, conversation_id),
            "preferences": await self._get_user_preferences(db, user_id),
            "summary": await self._get_conversation_summary(conversation_id),
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "message_count": len(
                    await self._get_recent_messages(db, conversation_id)
                ),
            },
        }

        # Cache for quick access
        await self.redis.setex(
            cache_key, self.short_term_ttl, json.dumps(context, default=str)
        )

        return context

    async def _get_recent_messages(
        self, db: AsyncSession, conversation_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get recent messages from a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            limit: Number of messages to retrieve (default: context_window)

        Returns:
            list[dict]: List of message dicts
        """
        limit = limit or self.context_window

        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(stmt)
        messages = result.scalars().all()

        # Reverse to chronological order and decrypt
        return [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": decrypt_data(msg.content_encrypted),
                "created_at": msg.created_at.isoformat(),
                "crisis_detected": msg.crisis_detected,
            }
            for msg in reversed(messages)
        ]

    async def _get_user_preferences(
        self, db: AsyncSession, user_id: int
    ) -> dict[str, Any]:
        """
        Get user preferences and context.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            dict: User preferences
        """
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return {}

        # Parse preferences if they exist
        preferences = {}
        if user.preferences_encrypted:
            try:
                prefs_json = decrypt_data(user.preferences_encrypted)
                preferences = json.loads(prefs_json)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse user preferences: {e}")

        # Add basic user info
        first_name = None
        if user.first_name_encrypted:
            try:
                first_name = decrypt_data(user.first_name_encrypted)
            except Exception:
                pass

        return {
            "first_name": first_name,
            "trust_level": user.trust_level.value,
            "subscription_tier": user.subscription_tier.value,
            "custom_preferences": preferences,
        }

    async def _get_conversation_summary(self, conversation_id: int) -> str | None:
        """
        Get conversation summary from cache.

        Args:
            conversation_id: Conversation ID

        Returns:
            str | None: Summary text if available
        """
        summary_key = f"summary:conv:{conversation_id}"
        summary = await self.redis.get(summary_key)
        return summary

    async def save_conversation_summary(
        self, conversation_id: int, summary: str, ttl: int = 86400
    ) -> None:
        """
        Save a conversation summary to cache.

        Args:
            conversation_id: Conversation ID
            summary: Summary text
            ttl: Time to live in seconds (default: 24 hours)
        """
        summary_key = f"summary:conv:{conversation_id}"
        await self.redis.setex(summary_key, ttl, summary)

        logger.info(f"Conversation summary saved", extra={"conversation_id": conversation_id})

    async def update_user_preference(
        self, db: AsyncSession, user_id: int, key: str, value: Any
    ) -> None:
        """
        Update a user preference.

        Args:
            db: Database session
            user_id: User ID
            key: Preference key
            value: Preference value
        """
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get current preferences
        preferences = {}
        if user.preferences_encrypted:
            try:
                prefs_json = decrypt_data(user.preferences_encrypted)
                preferences = json.loads(prefs_json)
            except Exception:
                pass

        # Update preference
        preferences[key] = value

        # Save back
        user.preferences_encrypted = encrypt_data(json.dumps(preferences))
        await db.flush()

        # Invalidate cache
        cache_keys = await self.redis.keys(f"context:user:{user_id}:*")
        if cache_keys:
            await self.redis.delete(*cache_keys)

        logger.info(
            f"User preference updated",
            extra={"user_id": user_id, "key": key},
        )

    async def get_message_history(
        self,
        db: AsyncSession,
        conversation_id: int,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get message history for a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            since: Get messages since this datetime
            limit: Maximum number of messages

        Returns:
            list[dict]: Message history
        """
        stmt = select(Message).where(Message.conversation_id == conversation_id)

        if since:
            stmt = stmt.where(Message.created_at >= since)

        stmt = stmt.order_by(Message.created_at.desc()).limit(limit)

        result = await db.execute(stmt)
        messages = result.scalars().all()

        return [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": decrypt_data(msg.content_encrypted),
                "created_at": msg.created_at.isoformat(),
                "direction": msg.direction.value,
                "model_used": msg.model_used,
                "crisis_detected": msg.crisis_detected,
            }
            for msg in reversed(messages)
        ]

    async def get_conversation_stats(
        self, db: AsyncSession, conversation_id: int
    ) -> dict[str, Any]:
        """
        Get statistics about a conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            dict: Conversation statistics
        """
        from sqlalchemy import func

        # Get message count
        stmt = select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        result = await db.execute(stmt)
        message_count = result.scalar() or 0

        # Get crisis event count
        stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id, Message.crisis_detected == True
        )
        result = await db.execute(stmt)
        crisis_count = result.scalar() or 0

        # Get first and last message times
        stmt = (
            select(func.min(Message.created_at), func.max(Message.created_at))
            .where(Message.conversation_id == conversation_id)
        )
        result = await db.execute(stmt)
        first_at, last_at = result.one()

        return {
            "conversation_id": conversation_id,
            "message_count": message_count,
            "crisis_events": crisis_count,
            "first_message_at": first_at.isoformat() if first_at else None,
            "last_message_at": last_at.isoformat() if last_at else None,
            "duration_hours": (
                (last_at - first_at).total_seconds() / 3600 if first_at and last_at else 0
            ),
        }

    async def invalidate_context_cache(self, user_id: int, conversation_id: int) -> None:
        """
        Invalidate cached conversation context.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
        """
        cache_key = f"context:user:{user_id}:conv:{conversation_id}"
        await self.redis.delete(cache_key)

        logger.debug(f"Context cache invalidated", extra={"cache_key": cache_key})

    async def store_temporary_data(
        self, key: str, data: Any, ttl: int = 300
    ) -> None:
        """
        Store temporary data in Redis (e.g., verification codes, session data).

        Args:
            key: Cache key
            data: Data to store (will be JSON serialized)
            ttl: Time to live in seconds (default: 5 minutes)
        """
        await self.redis.setex(key, ttl, json.dumps(data, default=str))

    async def get_temporary_data(self, key: str) -> Any | None:
        """
        Retrieve temporary data from Redis.

        Args:
            key: Cache key

        Returns:
            Any | None: Stored data or None if not found
        """
        data = await self.redis.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return None


async def get_memory_service(
    redis_client: RedisClient = None,
) -> MemoryService:
    """Dependency to get memory service."""
    if redis_client is None:
        redis_client = get_redis_client()
    return MemoryService(redis_client)
