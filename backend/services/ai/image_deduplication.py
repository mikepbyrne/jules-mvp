"""
Image deduplication service to prevent duplicate AI processing.

Uses perceptual hashing to detect duplicate/similar images.
"""
import imagehash
from PIL import Image
import aiohttp
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ImageDeduplicationService:
    """Detect and prevent duplicate image processing."""

    def __init__(self, redis_client, cache_ttl: int = 86400):
        self.redis = redis_client
        self.cache_ttl = cache_ttl  # 24 hours

    async def check_duplicate(
        self,
        image_url: str,
        household_id: str,
        correlation_id: str
    ) -> Optional[Dict]:
        """
        Check if image was recently processed.

        Returns cached result if duplicate found, None otherwise.
        """
        try:
            # Download and hash image
            phash = await self._get_perceptual_hash(image_url)

            cache_key = f"image_hash:{household_id}:{phash}"

            # Check cache
            cached_result = await self.redis.get(cache_key)

            if cached_result:
                logger.info("duplicate_image_detected",
                           correlation_id=correlation_id,
                           household_id=household_id,
                           hash=phash)

                import json
                return json.loads(cached_result)

            logger.info("unique_image",
                       correlation_id=correlation_id,
                       hash=phash)

            return None

        except Exception as e:
            logger.error("dedup_check_failed",
                        correlation_id=correlation_id,
                        error=str(e))
            # Don't block processing if dedup fails
            return None

    async def cache_result(
        self,
        image_url: str,
        household_id: str,
        result: Dict,
        correlation_id: str
    ):
        """Cache extraction result for deduplication."""
        try:
            phash = await self._get_perceptual_hash(image_url)
            cache_key = f"image_hash:{household_id}:{phash}"

            import json
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(result, default=str)
            )

            logger.info("result_cached",
                       correlation_id=correlation_id,
                       hash=phash)

        except Exception as e:
            logger.error("cache_failed",
                        correlation_id=correlation_id,
                        error=str(e))

    async def _get_perceptual_hash(self, image_url: str) -> str:
        """Download image and compute perceptual hash."""
        # Download image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download image: {response.status}")

                image_data = await response.read()

        # Open with PIL
        from io import BytesIO
        image = Image.open(BytesIO(image_data))

        # Compute perceptual hash (resistant to minor changes)
        phash = imagehash.phash(image)

        return str(phash)
