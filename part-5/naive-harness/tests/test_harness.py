"""Tests for the naive harness."""

import re
from unittest.mock import MagicMock, patch

from naive_harness import DEFAULT_SYSTEM_PROMPT, run
from naive_harness.harness import SEARCH_PATTERN, SEARCH_RESULTS_PATTERN
from naive_harness.llm import StubClient


class TestDefaultSystemPrompt:
    def test_system_prompt_exists(self):
        assert DEFAULT_SYSTEM_PROMPT is not None
        assert len(DEFAULT_SYSTEM_PROMPT) > 0

    def test_system_prompt_contains_search_protocol(self):
        assert "<search>" in DEFAULT_SYSTEM_PROMPT
        assert "</search>" in DEFAULT_SYSTEM_PROMPT

    def test_system_prompt_contains_search_results_expectation(self):
        assert "<search-results>" in DEFAULT_SYSTEM_PROMPT


class TestSearchPatterns:
    def test_search_pattern_matches(self):
        text = "Some text <search>weather in Tokyo</search> more text"
        match = SEARCH_PATTERN.search(text)
        assert match is not None
        assert match.group(1) == "weather in Tokyo"

    def test_search_pattern_no_match(self):
        text = "No search tags here"
        match = SEARCH_PATTERN.search(text)
        assert match is None

    def test_search_results_pattern_matches(self):
        text = "Before <search-results>result 1\nresult 2</search-results> after"
        match = SEARCH_RESULTS_PATTERN.search(text)
        assert match is not None
        assert "result 1" in match.group(1)


class TestRun:
    def test_run_no_search_returns_response(self):
        """When model returns no search tag, return response directly."""
        stub = StubClient(responses=["Direct answer"])

        result = run(
            prompt="What is 2+2?",
            api_key="",
            api_url="http://localhost:11434/v1",
            searxng_url="http://localhost:44433",
            model="gemma4:e2b",
            llm_client=stub,
        )

        assert result == "Direct answer"
        # Verify only one call was made (no search loop)
        assert stub.call_count == 1

    def test_run_with_search_calls_searxng(self):
        """When model returns only search tag, delegate to SearXNG and retry."""
        stub = StubClient(responses=[
            "<search>weather Tokyo</search>",
            "The weather in Tokyo is sunny.",
        ])

        with patch("naive_harness.harness.SearchProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.search_multiple.return_value = ("Tokyo: 22°C, sunny", 1)
            mock_provider_class.return_value = mock_provider

            result = run(
                prompt="What is the weather in Tokyo?",
                api_key="",
                api_url="http://localhost:11434/v1",
                searxng_url="http://localhost:44433",
                model="gemma4:e2b",
                llm_client=stub,
            )

            assert result == "The weather in Tokyo is sunny."
            # Verify two calls were made (search + final)
            assert stub.call_count == 2
            # Verify SearchProvider was called
            mock_provider_class.assert_called_once_with("http://localhost:44433")
            mock_provider.search_multiple.assert_called_once_with(["weather Tokyo"])

    def test_run_no_history_maintained(self):
        """Each call should be stateless — no message accumulation."""
        stub = StubClient(responses=["Answer"])

        run(
            prompt="Test prompt",
            api_key="",
            api_url="http://localhost:11434/v1",
            searxng_url="http://localhost:44433",
            llm_client=stub,
        )

        # Check what was sent to the LLM
        messages = stub.last_messages

        # Should only have system + user, no history accumulation
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test prompt"
