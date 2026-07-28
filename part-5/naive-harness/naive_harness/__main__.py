"""CLI entry point for naive-harness."""

import argparse
import sys

from .harness import run, DEFAULT_SYSTEM_PROMPT


def main():
    """Parse arguments and run the harness."""
    parser = argparse.ArgumentParser(
        description="Naive OpenAI harness with SearXNG search delegation",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="OpenAI-compatible API key (optional for local models like Ollama)",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:11434/v1",
        help="OpenAI-compatible API base URL (default: http://localhost:11434/v1)",
    )
    parser.add_argument(
        "--searxng-url",
        required=True,
        help="SearXNG instance URL (e.g. http://localhost:44433)",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="User query prompt",
    )
    parser.add_argument(
        "--model",
        default="gemma4:e2b",
        help="Model name (default: gemma4:e2b)",
    )
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Override the default system prompt",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens for the response (default: 1024)",
    )

    args = parser.parse_args()

    try:
        run(
            prompt=args.prompt,
            api_key=args.api_key,
            api_url=args.api_url,
            searxng_url=args.searxng_url,
            model=args.model,
            system_prompt=args.system_prompt,
            max_tokens=args.max_tokens,
        )
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
