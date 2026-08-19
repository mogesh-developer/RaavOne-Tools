"""Search execution tools."""

import asyncio
from typing import Any, Dict, Type, List
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.search.provider import SearchProvider


class WebSearchInput(BaseModel):
    """Input parameters for web search with additional filters."""
    query: str = Field(..., description="The search query text (e.g. 'Python 3.12 features')")
    max_results: int = Field(5, description="Maximum number of search results to return (default: 5)")
    limit: int | None = Field(None, description="Maximum number of results to return (overrides max_results)")
    domains: List[str] | None = Field(None, description="List of domains to restrict the search")
    recency: str | None = Field(None, description="Recency filter like '7d', '1w', '1m', '1y'")


class WebSearchTool(BaseTool[SearchProvider]):
    """Tool that queries the web via DuckDuckGo and returns structured search results."""

    name: str = "web_search"
    description: str = "Search the web for news, features, references, or repositories and get structured results."
    input_schema: Type[BaseModel] = WebSearchInput

    async def execute(
        self,
        query: str,
        max_results: int = 5,
        limit: int | None = None,
        domains: List[str] | None = None,
        recency: str | None = None,
    ) -> Dict[str, Any]:
        """Perform search query asynchronously with optional filters."""
        if not self.provider:
            raise ProviderError("SearchProvider has not been assigned to this tool.")

        # Run the blocking search call in an executor to prevent event loop blocking
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            self.provider.search_text,
            query,
            max_results,
            limit,
            domains,
            recency,
        )

        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results),
        }


# New tool: Open URL
class SearchOpenInput(BaseModel):
    url: str = Field(..., description="URL to open and fetch content from")

class SearchOpenTool(BaseTool[SearchProvider]):
    name: str = "search_open"
    description: str = "Open a URL and retrieve its raw HTML/text content."
    input_schema: Type[BaseModel] = SearchOpenInput

    async def execute(self, url: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("SearchProvider not assigned.")
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(None, self.provider.open_url, url)
        return {"status": "success", "url": url, "content": content}

# New tool: Extract (currently returns full page)
class SearchExtractInput(BaseModel):
    url: str = Field(..., description="URL to fetch and extract content from")

class SearchExtractTool(BaseTool[SearchProvider]):
    name: str = "search_extract"
    description: str = "Fetch a URL and extract relevant text (placeholder implementation)."
    input_schema: Type[BaseModel] = SearchExtractInput

    async def execute(self, url: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("SearchProvider not assigned.")
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(None, self.provider.fetch_and_extract, url)
        return {"status": "success", "url": url, "extracted": content}

# New tool: Suggest Queries
class SearchSuggestInput(BaseModel):
    query: str = Field(..., description="Base query string to get suggestions for")

class SearchSuggestTool(BaseTool[SearchProvider]):
    name: str = "search_suggest"
    description: str = "Provide related query suggestions based on a base query."
    input_schema: Type[BaseModel] = SearchSuggestInput

    async def execute(self, query: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("SearchProvider not assigned.")
        loop = asyncio.get_running_loop()
        suggestions = await loop.run_in_executor(None, self.provider.suggest, query)
        return {"status": "success", "query": query, "suggestions": suggestions}
