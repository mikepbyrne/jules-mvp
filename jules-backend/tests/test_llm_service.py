"""Tests for LLM service."""

import pytest

from src.services.llm_service import LLMService


@pytest.mark.asyncio
class TestLLMService:
    """Test suite for LLM service."""

    async def test_generate_response_anthropic(self, mocker):
        """Test Anthropic response generation."""
        # Mock Anthropic response
        mock_response = mocker.Mock()
        mock_response.content = [mocker.Mock(text="Hello! How can I help you?")]
        mock_response.usage = mocker.Mock(input_tokens=50, output_tokens=50)
        mock_response.stop_reason = "end_turn"

        mock_client = mocker.AsyncMock()
        mock_client.messages.create.return_value = mock_response

        # Patch the client
        mocker.patch.object(LLMService, "anthropic_client", mock_client)

        service = LLMService()
        result = await service.generate_response(
            messages=[{"role": "user", "content": "Hello"}],
            system_prompt="You are a helpful assistant.",
            provider="anthropic",
        )

        assert result["content"] == "Hello! How can I help you?"
        assert result["tokens_used"] == 100
        assert result["provider"] == "anthropic"
        assert "latency_ms" in result

    async def test_generate_response_openai(self, mocker):
        """Test OpenAI response generation."""
        # Mock OpenAI response
        mock_choice = mocker.Mock()
        mock_choice.message.content = "I'm here to help!"
        mock_choice.finish_reason = "stop"

        mock_response = mocker.Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mocker.Mock(total_tokens=75)

        mock_client = mocker.AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        mocker.patch.object(LLMService, "openai_client", mock_client)

        service = LLMService()
        result = await service.generate_response(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are helpful.",
            provider="openai",
        )

        assert result["content"] == "I'm here to help!"
        assert result["tokens_used"] == 75
        assert result["provider"] == "openai"

    async def test_generate_response_default_provider(self, mocker):
        """Test using default provider."""
        mock_response = mocker.Mock()
        mock_response.content = [mocker.Mock(text="Default response")]
        mock_response.usage = mocker.Mock(input_tokens=10, output_tokens=10)
        mock_response.stop_reason = "end_turn"

        mock_client = mocker.AsyncMock()
        mock_client.messages.create.return_value = mock_response

        mocker.patch.object(LLMService, "anthropic_client", mock_client)

        service = LLMService()
        service.default_provider = "anthropic"

        result = await service.generate_response(
            messages=[{"role": "user", "content": "Test"}]
        )

        assert "content" in result
        assert result["provider"] == "anthropic"

    async def test_generate_response_invalid_provider(self, mocker):
        """Test invalid provider raises error."""
        service = LLMService()

        with pytest.raises(ValueError, match="Unsupported provider"):
            await service.generate_response(
                messages=[{"role": "user", "content": "Test"}],
                provider="invalid",
            )

    async def test_moderate_content(self, mocker):
        """Test content moderation."""
        # Mock moderation response
        mock_result = mocker.Mock()
        mock_result.flagged = True
        mock_result.categories.model_dump.return_value = {
            "hate": False,
            "violence": True,
            "self-harm": False,
        }
        mock_result.category_scores.model_dump.return_value = {
            "violence": 0.95,
        }

        mock_response = mocker.Mock()
        mock_response.results = [mock_result]

        mock_client = mocker.AsyncMock()
        mock_client.moderations.create.return_value = mock_response

        mocker.patch.object(LLMService, "openai_client", mock_client)

        service = LLMService()
        result = await service.moderate_content("violent text")

        assert result["flagged"] is True
        assert "violence" in result["categories"]
        assert result["category_scores"]["violence"] == 0.95

    async def test_moderate_content_failure(self, mocker):
        """Test moderation failure returns safe default."""
        mock_client = mocker.AsyncMock()
        mock_client.moderations.create.side_effect = Exception("API error")

        mocker.patch.object(LLMService, "openai_client", mock_client)

        service = LLMService()
        result = await service.moderate_content("test")

        # Should return safe default
        assert result["flagged"] is False
        assert result["categories"] == {}
