"""
Hybrid Redis/PostgreSQL state management.

Hot conversation state cached in Redis, persisted to PostgreSQL asynchronously.
"""
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class HybridStateManager:
    """Manages conversation state with Redis cache + PostgreSQL persistence."""

    def __init__(self, redis_client, db_session, ttl: int = 300):
        self.redis = redis_client
        self.db = db_session
        self.ttl = ttl  # 5 minutes
        self.background_tasks = asyncio.Queue()

    async def get_state(self, household_id: str, member_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get conversation state (Redis first, fallback to DB).

        Returns state dict or None if not found.
        """
        cache_key = self._get_cache_key(household_id, member_id)

        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            logger.info("state_cache_hit", household_id=household_id, member_id=member_id)
            return json.loads(cached)

        # Cache miss - query database
        logger.info("state_cache_miss", household_id=household_id, member_id=member_id)

        state = await self._load_from_db(household_id, member_id)

        if state:
            # Populate cache
            await self.redis.setex(
                cache_key,
                self.ttl,
                json.dumps(state, default=str)
            )

        return state

    async def update_state(
        self,
        household_id: str,
        state_data: Dict[str, Any],
        member_id: Optional[str] = None
    ):
        """
        Update conversation state (immediate cache, async DB persist).

        Optimizes for low latency by updating cache immediately.
        """
        cache_key = self._get_cache_key(household_id, member_id)

        # Update cache immediately
        await self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(state_data, default=str)
        )

        logger.info("state_cached", household_id=household_id, member_id=member_id)

        # Queue background DB persist
        await self.background_tasks.put({
            "action": "persist",
            "household_id": household_id,
            "member_id": member_id,
            "state_data": state_data
        })

    async def delete_state(self, household_id: str, member_id: Optional[str] = None):
        """Delete conversation state from cache and DB."""
        cache_key = self._get_cache_key(household_id, member_id)

        # Delete from cache
        await self.redis.delete(cache_key)

        # Queue background DB delete
        await self.background_tasks.put({
            "action": "delete",
            "household_id": household_id,
            "member_id": member_id
        })

        logger.info("state_deleted", household_id=household_id, member_id=member_id)

    async def process_background_tasks(self):
        """
        Background worker to persist state changes to database.

        Run as separate async task.
        """
        logger.info("background_worker_start")

        while True:
            try:
                task = await self.background_tasks.get()

                if task["action"] == "persist":
                    await self._persist_to_db(
                        task["household_id"],
                        task["member_id"],
                        task["state_data"]
                    )
                elif task["action"] == "delete":
                    await self._delete_from_db(
                        task["household_id"],
                        task["member_id"]
                    )

                self.background_tasks.task_done()

            except Exception as e:
                logger.error("background_task_failed", error=str(e))
                await asyncio.sleep(1)

    def _get_cache_key(self, household_id: str, member_id: Optional[str]) -> str:
        """Generate Redis cache key."""
        if member_id:
            return f"state:individual:{household_id}:{member_id}"
        return f"state:group:{household_id}"

    async def _load_from_db(self, household_id: str, member_id: Optional[str]) -> Optional[Dict]:
        """Load state from PostgreSQL."""
        from backend.models.conversation import ConversationState

        query = self.db.query(ConversationState).filter(
            ConversationState.household_id == household_id
        )

        if member_id:
            query = query.filter(ConversationState.member_id == member_id)
        else:
            query = query.filter(ConversationState.member_id.is_(None))

        state_record = await query.first()

        if not state_record:
            return None

        return {
            "id": state_record.id,
            "household_id": state_record.household_id,
            "member_id": state_record.member_id,
            "channel": state_record.channel,
            "current_flow": state_record.current_flow,
            "current_step": state_record.current_step,
            "flow_data": state_record.flow_data,
            "started_at": state_record.started_at,
            "last_activity_at": state_record.last_activity_at
        }

    async def _persist_to_db(
        self,
        household_id: str,
        member_id: Optional[str],
        state_data: Dict
    ):
        """Persist state to PostgreSQL."""
        from backend.models.conversation import ConversationState

        try:
            # Upsert state
            existing = await self._load_from_db(household_id, member_id)

            if existing:
                # Update
                await self.db.query(ConversationState).filter(
                    ConversationState.id == existing["id"]
                ).update({
                    "current_flow": state_data.get("current_flow"),
                    "current_step": state_data.get("current_step"),
                    "flow_data": state_data.get("flow_data"),
                    "last_activity_at": datetime.utcnow()
                })
            else:
                # Insert
                new_state = ConversationState(
                    household_id=household_id,
                    member_id=member_id,
                    channel=state_data.get("channel"),
                    current_flow=state_data.get("current_flow"),
                    current_step=state_data.get("current_step"),
                    flow_data=state_data.get("flow_data")
                )
                self.db.add(new_state)

            await self.db.commit()

            logger.info("state_persisted", household_id=household_id, member_id=member_id)

        except Exception as e:
            logger.error("state_persist_failed",
                        household_id=household_id,
                        member_id=member_id,
                        error=str(e))
            await self.db.rollback()

    async def _delete_from_db(self, household_id: str, member_id: Optional[str]):
        """Delete state from PostgreSQL."""
        from backend.models.conversation import ConversationState

        try:
            query = self.db.query(ConversationState).filter(
                ConversationState.household_id == household_id
            )

            if member_id:
                query = query.filter(ConversationState.member_id == member_id)
            else:
                query = query.filter(ConversationState.member_id.is_(None))

            await query.delete()
            await self.db.commit()

            logger.info("state_db_deleted", household_id=household_id, member_id=member_id)

        except Exception as e:
            logger.error("state_delete_failed",
                        household_id=household_id,
                        member_id=member_id,
                        error=str(e))
            await self.db.rollback()
