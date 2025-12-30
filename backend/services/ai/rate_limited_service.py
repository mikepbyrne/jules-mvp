"""
Rate-limited AI service with queue management.

Prevents API rate limit errors and cost spikes.
"""
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIRequest:
    """Queued AI request."""
    request_id: str
    image_url: str
    request_type: str  # 'recipe_extraction', 'pantry_scan', 'meal_suggestion'
    correlation_id: Optional[str] = None
    priority: int = 0  # Higher = more urgent


class RateLimitedAIService:
    """AI service with request queue and rate limiting."""

    def __init__(
        self,
        ai_client,
        max_concurrent: int = 5,
        max_retries_per_household: int = 3
    ):
        self.client = ai_client
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries_per_household

        # Semaphore for concurrent request limit
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Priority queue for requests
        self.queue = asyncio.PriorityQueue()

        # Track retry counts per household
        self.retry_counts: Dict[str, int] = {}

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "rate_limited": 0,
            "queued": 0
        }

    async def extract_recipe(
        self,
        image_url: str,
        household_id: str,
        correlation_id: str,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Extract recipe from image with rate limiting.

        Uses queue to prevent exceeding API limits.
        """
        # Check retry limit per household
        retry_count = self.retry_counts.get(household_id, 0)
        if retry_count >= self.max_retries:
            logger.warning("retry_limit_exceeded",
                          correlation_id=correlation_id,
                          household_id=household_id,
                          retries=retry_count)
            raise Exception(f"Maximum {self.max_retries} extraction attempts reached")

        # Add to queue
        request = AIRequest(
            request_id=correlation_id,
            image_url=image_url,
            request_type="recipe_extraction",
            correlation_id=correlation_id,
            priority=priority
        )

        self.metrics["queued"] += 1

        # Wait for slot in queue
        async with self.semaphore:
            self.metrics["total_requests"] += 1

            logger.info("ai_request_start",
                       correlation_id=correlation_id,
                       household_id=household_id,
                       queue_size=self.queue.qsize())

            try:
                result = await self._execute_extraction(image_url, correlation_id)

                # Reset retry count on success
                self.retry_counts[household_id] = 0
                self.metrics["successful"] += 1

                logger.info("ai_request_success",
                           correlation_id=correlation_id,
                           confidence=result.get("confidence"))

                return result

            except Exception as e:
                # Increment retry count
                self.retry_counts[household_id] = retry_count + 1
                self.metrics["failed"] += 1

                logger.error("ai_request_failed",
                            correlation_id=correlation_id,
                            household_id=household_id,
                            error=str(e),
                            retry_count=self.retry_counts[household_id])

                raise

    async def _execute_extraction(self, image_url: str, correlation_id: str) -> Dict:
        """Execute AI extraction with timeout."""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic()

        try:
            # Set timeout to 30 seconds
            response = await asyncio.wait_for(
                client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": image_url
                                }
                            },
                            {
                                "type": "text",
                                "text": """Extract recipe from this image. Return JSON:
{
  "title": "Recipe name",
  "ingredients": [{"quantity": "1", "unit": "cup", "item": "flour"}],
  "instructions": ["Step 1", "Step 2"],
  "prep_time": 15,
  "cook_time": 30,
  "servings": 4,
  "difficulty": "easy|medium|hard",
  "confidence": 0.95
}"""
                            }
                        ]
                    }),
                timeout=30
            )

            # Parse response
            import json
            content = response.content[0].text
            recipe_data = json.loads(content)

            return recipe_data

        except asyncio.TimeoutError:
            logger.error("ai_timeout", correlation_id=correlation_id)
            raise Exception("AI request timed out after 30 seconds")

        except Exception as e:
            logger.error("ai_error", correlation_id=correlation_id, error=str(e))
            raise

    async def get_metrics(self) -> Dict[str, int]:
        """Get AI service metrics."""
        return {
            **self.metrics,
            "queue_size": self.queue.qsize(),
            "available_slots": self.semaphore._value
        }
