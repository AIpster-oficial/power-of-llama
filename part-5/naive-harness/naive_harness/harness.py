"""Core harness orchestration — naive, stateless, search-aware."""

import re

from .console import console
from .llm import LLMClient, OpenAIClient
from .search import SearchProvider

DEFAULT_SYSTEM_PROMPT = (
    "Do not trust your training data.\n"
    "\n"
    "Whenever you want to search for an information. Output <search>{{search criteria}}</search> and halt the execution.\n"
    "\n"
    "Expect the result to be within the <search-results> tag."
)

SEARCH_PATTERN = re.compile(r"<search>(.*?)</search>")
SEARCH_RESULTS_PATTERN = re.compile(r"<search-results>(.*?)</search-results>", re.DOTALL)


def _extract_clean_criteria(search_matches: list[str]) -> list[str]:
    """Extract and clean search criteria from LLM response matches.

    Args:
        search_matches: List of raw search criteria from <search> tags.

    Returns:
        List of cleaned criteria strings.
    """
    return [_strip_search_tags_criteria(c) for c in search_matches]


def _wrap_results(results: str) -> str:
    """Wrap search results in <search-results> tags.

    Args:
        results: Raw search results string.

    Returns:
        Results wrapped in <search-results> tags.
    """
    return f"<search-results>{results}</search-results>"


def _strip_search_tags_criteria(raw: str) -> str:
    """Strip {{...}} template syntax from a single search criteria."""
    clean = raw.strip()
    if clean.startswith("{{") and clean.endswith("}}"):
        clean = clean[2:-2].strip()
    return clean


def run(
    prompt: str,
    api_key: str,
    api_url: str,
    searxng_url: str,
    *,
    model: str = "gemma4:e2b",
    system_prompt: str | None = None,
    max_tokens: int = 1024,
    llm_client: LLMClient | None = None,
) -> str:
    """Run the naive harness.

    Each call is stateless — no conversation history is maintained.
    If the model returns a <search> tag, the harness delegates to SearXNG
    and makes a fresh call with the results appended.

    Args:
        prompt: User input prompt.
        api_key: OpenAI-compatible API key.
        api_url: OpenAI-compatible API base URL (e.g. http://localhost:11434/v1).
        searxng_url: SearXNG instance URL (e.g. http://localhost:44433).
        model: Model name (default: gemma4:e2b).
        system_prompt: Override the default system prompt.
        max_tokens: Maximum tokens for the response.
        llm_client: Optional LLM client (creates OpenAIClient if not provided).

    Returns:
        The final text response from the model.
    """
    sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    current_prompt = prompt
    provider = SearchProvider(searxng_url)
    client = llm_client or OpenAIClient(api_key=api_key, base_url=api_url)

    while True:
        # Build messages fresh every time — no history
        messages = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        messages.append({"role": "user", "content": current_prompt})

        # Call LLM
        llm_response = client.complete(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
        )
        response = llm_response.content
        reasoning = llm_response.reasoning

        # Show reasoning if present
        if reasoning:
            console.thinking_block(reasoning)

        # Check for search protocol — ALWAYS search if any <search> tag exists
        search_matches = SEARCH_PATTERN.findall(response)

        if search_matches:
            # Delegate to SearXNG — harness extracts criteria, search handles iteration
            clean_criteria_list = _extract_clean_criteria(search_matches)
            combined_results, _ = provider.search_multiple(clean_criteria_list)

            # Wrap results and build new prompt (still no history)
            wrapped_results = _wrap_results(combined_results)
            current_prompt = wrapped_results
            continue

        # No search tag — return final response
        console.output(response)
        break

    return response
