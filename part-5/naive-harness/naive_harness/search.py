"""SearXNG search provider with full page fetching."""

import httpx
from html.parser import HTMLParser

from .console import console


class TextExtractor(HTMLParser):
    """Extract text content from HTML."""

    def __init__(self):
        super().__init__()
        self.text = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        # Skip scripts, styles, and other non-content elements
        if tag in ("script", "style", "noscript", "iframe", "nav", "footer", "header"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "iframe", "nav", "footer", "header"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)


class SearchProvider:
    """Handles SearXNG search and page fetching."""

    def __init__(self, searxng_url: str, max_results: int = 5, timeout: float = 10.0):
        """Initialize search provider.

        Args:
            searxng_url: SearXNG instance URL.
            max_results: Maximum number of results to return.
            timeout: Request timeout in seconds.
        """
        self.searxng_url = searxng_url
        self.max_results = max_results
        self.timeout = timeout

    def _console_search(self, query: str) -> None:
        """Print search query in blue."""
        console.search(query)

    def _console_search_results(self, count: int) -> None:
        """Print result count in blue."""
        console.search_results(count)

    def search(self, query: str) -> str:
        """Execute search and return formatted results with full page content.

        Args:
            query: Search query string.

        Returns:
            Formatted string with search results.
        """
        self._console_search(query)
        return self._execute_search(query)

    def search_multiple(self, queries: list[str]) -> tuple[str, int]:
        """Execute multiple searches and return combined results.

        Args:
            queries: List of search query strings.

        Returns:
            Tuple of (combined results string, total result count).
        """
        all_results = []
        total_count = 0
        for query in queries:
            self._console_search(query)
            result = self._execute_search(query)
            result_lines = [l for l in result.splitlines() if l.strip()]
            total_count += len(result_lines)
            all_results.append(result)
        combined = "\n\n".join(all_results)
        self._console_search_results(total_count)
        return combined, total_count

    def _execute_search(self, query: str) -> str:
        """Execute a single search and return formatted results.

        Args:
            query: Search query string.

        Returns:
            Formatted string with search results.
        """
        search_url = f"{self.searxng_url}/search"
        params = {
            "q": query,
            "format": "json",
            "engines": "google,bing,duckduckgo",
        }

        try:
            response = httpx.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            return f"Search failed: {exc}"

        results = data.get("results", [])
        if not results:
            return "No results found."

        lines = []
        for i, result in enumerate(results[:self.max_results], 1):
            title = result.get("title", "No title")
            result_url = result.get("url", "")
            snippet = result.get("content", "")

            lines.append(f"--- Result {i}: {title} ---")
            if result_url:
                lines.append(f"URL: {result_url}")
            if snippet:
                lines.append(f"Snippet: {snippet}")

            # Fetch full page content
            if result_url:
                page_text = self._fetch_page(result_url)
                if page_text:
                    lines.append(f"Content: {page_text}")
                else:
                    lines.append("Content: (could not fetch page)")
            else:
                lines.append("Content: (no URL)")

            lines.append("")

        return "\n".join(lines)

    def console_search(self, query: str) -> None:
        """Print search query in blue."""
        console.search(query)

    def _fetch_page(self, url: str) -> str:
        """Fetch a URL and extract its text content.

        Args:
            url: URL to fetch.

        Returns:
            Extracted text content.
        """
        console.search_url(url)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (NaiveHarness/1.0)"}
            response = httpx.get(url, headers=headers, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()

            extractor = TextExtractor()
            extractor.feed(response.text)
            text = " ".join(extractor.text)
            # Clean up whitespace
            text = " ".join(text.split())
            return text[:2000] if text else ""
        except httpx.HTTPError:
            return ""


# Module-level singleton
search_provider = SearchProvider(searxng_url="")
