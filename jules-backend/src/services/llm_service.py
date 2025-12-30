"""LLM service supporting multiple providers (Anthropic, OpenAI)."""

import time
from typing import Any, Literal

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from src.config import get_settings
from src.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class LLMService:
    """LLM service with support for multiple providers."""

    def __init__(self) -> None:
        """Initialize LLM service with configured providers."""
        self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.default_provider = settings.default_llm_provider
        self.default_model = settings.default_model

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        provider: Literal["anthropic", "openai"] | None = None,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Generate LLM response with timing and token tracking.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            provider: LLM provider to use
            model: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            dict: Response with content, tokens, latency, and model info
        """
        provider = provider or self.default_provider
        model = model or self.default_model

        start_time = time.time()

        try:
            if provider == "anthropic":
                result = await self._generate_anthropic(
                    messages, system_prompt, model, max_tokens, temperature
                )
            elif provider == "openai":
                result = await self._generate_openai(
                    messages, system_prompt, model, max_tokens, temperature
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            latency_ms = int((time.time() - start_time) * 1000)
            result["latency_ms"] = latency_ms

            logger.info(
                f"LLM response generated",
                extra={
                    "provider": provider,
                    "model": model,
                    "tokens": result.get("tokens_used"),
                    "latency_ms": latency_ms,
                },
            )

            return result

        except Exception as e:
            logger.error(
                f"LLM generation failed",
                extra={"provider": provider, "model": model, "error": str(e)},
                exc_info=True,
            )
            raise

    async def _generate_anthropic(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        """Generate response using Anthropic Claude."""
        # Convert messages to Anthropic format
        anthropic_messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]

        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=anthropic_messages,
        )

        return {
            "content": response.content[0].text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "model": model,
            "provider": "anthropic",
            "finish_reason": response.stop_reason,
        }

    async def _generate_openai(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        """Generate response using OpenAI."""
        # Add system message if provided
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})

        openai_messages.extend([{"role": msg["role"], "content": msg["content"]} for msg in messages])

        response = await self.openai_client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=openai_messages,
        )

        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens,
            "model": model,
            "provider": "openai",
            "finish_reason": response.choices[0].finish_reason,
        }

    async def moderate_content(self, text: str) -> dict[str, Any]:
        """
        Use OpenAI's moderation API to check for harmful content.

        Args:
            text: Content to moderate

        Returns:
            dict: Moderation results
        """
        try:
            response = await self.openai_client.moderations.create(input=text)
            result = response.results[0]

            return {
                "flagged": result.flagged,
                "categories": {
                    category: flagged
                    for category, flagged in result.categories.model_dump().items()
                    if flagged
                },
                "category_scores": result.category_scores.model_dump(),
            }

        except Exception as e:
            logger.error(f"Content moderation failed: {e}", exc_info=True)
            # Return safe default if moderation fails
            return {"flagged": False, "categories": {}, "category_scores": {}}


# Global LLM service instance
llm_service = LLMService()


async def get_llm_service() -> LLMService:
    """Dependency to get LLM service."""
    return llm_service
