"""
Recipe extraction saga with rollback support.

Handles multi-step workflow:
1. Upload image to S3
2. Extract recipe with AI
3. Save to database
4. Notify user

If any step fails, previous steps are rolled back.
"""
from typing import Dict, Any
import uuid
from .base import Saga, SagaContext, SagaStep
import logging

logger = logging.getLogger(__name__)


class RecipeExtractionSaga(Saga):
    """Saga for recipe extraction workflow."""

    def __init__(self, storage_service, ai_service, recipe_service, notification_service):
        super().__init__()
        self.storage = storage_service
        self.ai = ai_service
        self.recipe = recipe_service
        self.notification = notification_service

    async def execute_extraction(
        self,
        image_data: bytes,
        household_id: str,
        member_id: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Execute recipe extraction with saga pattern."""

        saga_id = str(uuid.uuid4())
        context = self.create_context(saga_id)

        # Track state for rollback
        image_url = None
        recipe_id = None

        # Step 1: Upload image
        async def upload_image():
            nonlocal image_url
            image_url = await self.storage.upload_file(
                image_data,
                f"recipes/{household_id}/{saga_id}.jpg"
            )
            logger.info("image_uploaded", correlation_id=correlation_id,
                       image_url=image_url)
            return image_url

        async def delete_image():
            if image_url:
                await self.storage.delete_file(image_url)
                logger.info("image_deleted", correlation_id=correlation_id,
                           image_url=image_url)

        context.steps.append(SagaStep(
            name="upload_image",
            execute=upload_image,
            compensate=delete_image
        ))

        # Step 2: Extract recipe with AI
        async def extract_recipe():
            extraction_result = await self.ai.extract_recipe(image_url)
            logger.info("recipe_extracted", correlation_id=correlation_id,
                       confidence=extraction_result.get("confidence"))
            return extraction_result

        # No compensation needed for read operation

        context.steps.append(SagaStep(
            name="extract_recipe",
            execute=extract_recipe,
            compensate=None
        ))

        # Step 3: Save to database
        async def save_recipe():
            nonlocal recipe_id
            recipe_data = context.completed_steps[1].result
            recipe_id = await self.recipe.save_family_recipe(
                household_id=household_id,
                recipe_data=recipe_data,
                original_file_url=image_url,
                submitted_by_id=member_id
            )
            logger.info("recipe_saved", correlation_id=correlation_id,
                       recipe_id=recipe_id)
            return recipe_id

        async def delete_recipe():
            if recipe_id:
                await self.recipe.soft_delete_recipe(recipe_id)
                logger.info("recipe_deleted", correlation_id=correlation_id,
                           recipe_id=recipe_id)

        context.steps.append(SagaStep(
            name="save_recipe",
            execute=save_recipe,
            compensate=delete_recipe
        ))

        # Step 4: Notify user
        async def notify_success():
            recipe_data = context.completed_steps[1].result
            await self.notification.send_recipe_confirmation(
                member_id=member_id,
                recipe_title=recipe_data.get("title"),
                recipe_id=recipe_id
            )
            logger.info("user_notified", correlation_id=correlation_id,
                       member_id=member_id)

        # No compensation for notification

        context.steps.append(SagaStep(
            name="notify_user",
            execute=notify_success,
            compensate=None
        ))

        # Execute saga
        try:
            await self.orchestrator.execute(context)

            return {
                "success": True,
                "recipe_id": recipe_id,
                "image_url": image_url,
                "saga_id": saga_id
            }

        except Exception as e:
            # Rollback already happened in orchestrator
            logger.error("recipe_extraction_failed", correlation_id=correlation_id,
                        saga_id=saga_id, error=str(e))

            # Notify user of failure
            await self.notification.send_recipe_failure(
                member_id=member_id,
                error_message="extraction_failed"
            )

            return {
                "success": False,
                "error": str(e),
                "saga_id": saga_id
            }
