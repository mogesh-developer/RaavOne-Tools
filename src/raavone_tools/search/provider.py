"""Search provider for querying search engines."""

from typing import Any, Dict, List
from duckduckgo_search import DDGS

from raavone_tools.base import BaseProvider


class SearchProvider(BaseProvider):
    """Resource provider that interfaces with DuckDuckGo Search."""

    def __init__(self) -> None:
        """Initialize the search provider."""
        pass

    async def initialize(self) -> None:
        """Create the DuckDuckGo Search client instance."""
        pass

    async def close(self) -> None:
        """Close the search provider session."""
        pass

    def search_text(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Synchronously query DDG text search and return formatted dict results."""
        results = []
        with DDGS() as ddgs:
            ddg_results = ddgs.text(query, max_results=max_results)
            if ddg_results:
                for r in ddg_results:
                    results.append({
                        "title": r.get("title") or "",
                        "url": r.get("href") or "",
                        "snippet": r.get("body") or ""
                    })
        return results
