"""LLM client — stub/interface to LLM providers."""

from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    reasoning: str = ""


class LLMClient(Protocol):
    """Protocol for LLM clients."""

    def complete(
        self,
        messages: list[dict],
        *,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse: ...


class OpenAIClient:
    """OpenAI-compatible LLM client."""

    def __init__(self, api_key: str, base_url: str, temperature: float = 0.9):
        """Initialize the client.

        Args:
            api_key: API key.
            base_url: API base URL.
            temperature: Default temperature for completions.
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.temperature = temperature

    def complete(
        self,
        messages: list[dict],
        *,
        model: str,
        max_tokens: int,
        temperature: float | None = None,
    ) -> LLMResponse:
        """Complete a prompt.

        Args:
            messages: List of message dicts.
            model: Model name.
            max_tokens: Max tokens.
            temperature: Override default temperature.

        Returns:
            LLMResponse with content and reasoning.
        """
        temp = temperature if temperature is not None else self.temperature
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temp,
        )
        choice = completion.choices[0]
        content = choice.message.content or ""
        reasoning = getattr(choice.message, "reasoning", None) or ""
        return LLMResponse(content=content, reasoning=reasoning)


class StubClient:
    """Stub LLM client for testing."""

    def __init__(self, responses: list[str] | None = None):
        """Initialize with optional list of responses.

        Args:
            responses: List of responses to return in order.
        """
        self.responses = responses or []
        self.call_count = 0
        self.last_messages: list[dict] | None = None

    def complete(
        self,
        messages: list[dict],
        *,
        model: str,
        max_tokens: int,
        temperature: float = 0.9,
    ) -> LLMResponse:
        """Return next stub response."""
        self.last_messages = messages
        if self.responses:
            response = self.responses[self.call_count % len(self.responses)]
        else:
            response = "Stub response"
        self.call_count += 1
        return LLMResponse(content=response, reasoning="")
