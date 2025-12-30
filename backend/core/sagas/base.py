"""
Saga pattern implementation for distributed transactions.

Provides rollback mechanism when workflows span multiple services.
"""
from typing import Callable, List, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SagaStep:
    """A single step in a saga with optional compensation."""
    name: str
    execute: Callable
    compensate: Optional[Callable] = None
    result: Any = None


@dataclass
class SagaContext:
    """Context for saga execution."""
    saga_id: str
    steps: List[SagaStep] = field(default_factory=list)
    completed_steps: List[SagaStep] = field(default_factory=list)
    failed: bool = False
    error: Optional[Exception] = None


class SagaOrchestrator:
    """Orchestrates saga execution with automatic rollback on failure."""

    async def execute(self, context: SagaContext) -> SagaContext:
        """Execute saga steps in order, rollback on failure."""

        try:
            for step in context.steps:
                logger.info("saga_step_start", saga_id=context.saga_id, step=step.name)

                # Execute step
                step.result = await step.execute()
                context.completed_steps.append(step)

                logger.info("saga_step_complete", saga_id=context.saga_id, step=step.name)

        except Exception as e:
            logger.error("saga_failed", saga_id=context.saga_id,
                        step=step.name, error=str(e))
            context.failed = True
            context.error = e

            # Rollback completed steps in reverse order
            await self._rollback(context)
            raise

        return context

    async def _rollback(self, context: SagaContext):
        """Rollback completed steps in reverse order."""
        logger.info("saga_rollback_start", saga_id=context.saga_id,
                   steps_to_rollback=len(context.completed_steps))

        for step in reversed(context.completed_steps):
            if step.compensate:
                try:
                    logger.info("saga_compensate", saga_id=context.saga_id, step=step.name)
                    await step.compensate()
                except Exception as e:
                    logger.error("saga_compensate_failed", saga_id=context.saga_id,
                               step=step.name, error=str(e))
                    # Continue rollback even if compensation fails

        logger.info("saga_rollback_complete", saga_id=context.saga_id)


class Saga:
    """Base class for saga definitions."""

    def __init__(self):
        self.orchestrator = SagaOrchestrator()

    def create_context(self, saga_id: str) -> SagaContext:
        """Create new saga context."""
        return SagaContext(saga_id=saga_id)

    async def execute(self, context: SagaContext) -> SagaContext:
        """Execute saga."""
        return await self.orchestrator.execute(context)
