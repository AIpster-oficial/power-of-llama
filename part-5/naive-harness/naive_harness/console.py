"""Console output handler — centralizes all layout and color."""


class Console:
    """Handles all console output with consistent formatting and colors."""

    # ANSI color codes
    GREY = "\033[90m"
    BLUE = "\033[94m"
    WHITE = "\033[37m"
    RESET = "\033[0m"

    def thinking(self, text: str) -> None:
        """Print reasoning/thinking text in grey."""
        print(f"{self.GREY}{text}{self.RESET}")

    def thinking_block(self, text: str) -> None:
        """Print a thinking block with reasoning text in grey."""
        print(f"{self.GREY}{text}{self.RESET}\n")

    def search(self, query: str) -> None:
        """Print search query in blue."""
        print(f"{self.BLUE}Search for {query} ...{self.RESET}")

    def search_url(self, url: str) -> None:
        """Print URL fetching in blue."""
        print(f"{self.BLUE}Fetching {url} ...{self.RESET}")

    def search_results(self, count: int) -> None:
        """Print result count in blue."""
        print(f"{self.BLUE}Found {count} results{self.RESET}")

    def blank_line(self) -> None:
        """Print a blank line."""
        print()

    def output(self, text: str) -> None:
        """Print final response in white."""
        print(f"{self.WHITE}{text}{self.RESET}")


# Module-level singleton
console = Console()
