"""
SMS batch sender with rate limiting.

Prevents message loss at scale by respecting Twilio's 100 messages/second limit.
"""
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SMSMessage:
    """SMS message data."""
    to: str
    body: str
    from_number: str = None
    media_url: str = None
    correlation_id: str = None


class BatchSMSSender:
    """Batch SMS sender with rate limiting."""

    def __init__(
        self,
        sms_provider,
        rate_limit: int = 80,  # Under Twilio's 100/sec
        retry_attempts: int = 3
    ):
        self.provider = sms_provider
        self.rate_limit = rate_limit
        self.retry_attempts = retry_attempts
        self.queue = asyncio.Queue()
        self.stats = {
            "sent": 0,
            "failed": 0,
            "retried": 0
        }

    async def send_batch(self, messages: List[SMSMessage]) -> Dict[str, Any]:
        """
        Send batch of SMS messages with rate limiting.

        Returns summary of sent/failed messages.
        """
        logger.info("batch_send_start", total_messages=len(messages))

        # Add messages to queue
        for msg in messages:
            await self.queue.put(msg)

        results = {
            "success": [],
            "failed": []
        }

        # Process queue in rate-limited batches
        while not self.queue.empty():
            batch = []

            # Get up to rate_limit messages
            for _ in range(self.rate_limit):
                if self.queue.empty():
                    break
                batch.append(await self.queue.get())

            # Send batch concurrently
            batch_results = await asyncio.gather(
                *[self._send_with_retry(msg) for msg in batch],
                return_exceptions=True
            )

            # Collect results
            for msg, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results["failed"].append({
                        "to": msg.to,
                        "error": str(result)
                    })
                    self.stats["failed"] += 1
                else:
                    results["success"].append({
                        "to": msg.to,
                        "message_id": result
                    })
                    self.stats["sent"] += 1

            # Wait 1 second before next batch (rate limit window)
            if not self.queue.empty():
                await asyncio.sleep(1)

        logger.info("batch_send_complete",
                   sent=self.stats["sent"],
                   failed=self.stats["failed"],
                   retried=self.stats["retried"])

        return results

    async def _send_with_retry(self, message: SMSMessage) -> str:
        """Send single message with retry logic."""
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                if message.media_url:
                    message_id = await self.provider.send_media_message(
                        to=message.to,
                        body=message.body,
                        media_url=message.media_url,
                        from_number=message.from_number
                    )
                else:
                    message_id = await self.provider.send_message(
                        to=message.to,
                        body=message.body,
                        from_number=message.from_number
                    )

                if attempt > 0:
                    self.stats["retried"] += 1

                logger.info("sms_sent",
                           correlation_id=message.correlation_id,
                           to=message.to,
                           attempt=attempt + 1)

                return message_id

            except Exception as e:
                last_error = e
                logger.warning("sms_send_failed",
                             correlation_id=message.correlation_id,
                             to=message.to,
                             attempt=attempt + 1,
                             error=str(e))

                # Exponential backoff
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)

        # All retries exhausted
        logger.error("sms_send_exhausted",
                    correlation_id=message.correlation_id,
                    to=message.to,
                    attempts=self.retry_attempts,
                    error=str(last_error))

        raise last_error


class SMSScheduler:
    """Schedule SMS sends to avoid peak traffic times."""

    def __init__(self, batch_sender: BatchSMSSender):
        self.batch_sender = batch_sender

    async def schedule_weekly_planning_messages(
        self,
        households: List[Dict],
        send_time: str = "09:00"  # Sunday 9am
    ):
        """
        Schedule weekly planning messages across households.

        Spreads sends over 15 minutes to avoid spike.
        """
        total = len(households)
        batch_size = 100  # 100 households per minute

        logger.info("schedule_weekly_planning",
                   total_households=total,
                   batch_size=batch_size)

        for i in range(0, total, batch_size):
            batch = households[i:i + batch_size]

            # Create messages for batch
            messages = []
            for household in batch:
                for member in household["members"]:
                    if member["receives_group_messages"]:
                        messages.append(SMSMessage(
                            to=member["phone_number"],
                            body=self._generate_planning_message(household),
                            correlation_id=f"weekly_{household['id']}"
                        ))

            # Send batch
            await self.batch_sender.send_batch(messages)

            # Wait 1 minute before next batch
            if i + batch_size < total:
                await asyncio.sleep(60)

        logger.info("schedule_complete", total_sent=total * 3)  # Avg 3 members

    def _generate_planning_message(self, household: Dict) -> str:
        """Generate weekly planning message."""
        return f"""Good morning {household['name']} family! 🌞

Time to plan meals for the week. What sounds good?

Reply with meal ideas or "SUGGEST" for AI recommendations.

Reply STOP to opt out."""
