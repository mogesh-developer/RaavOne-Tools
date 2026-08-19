"""Search execution tools."""

import asyncio
from typing import Any, Dict, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.search.provider import SearchProvider


class WebSearchInput(BaseModel):
    """Input parameters for web search."""
    query: str = Field(..., description="The search query text (e.g. 'Python 3.12 features')")
    max_results: int = Field(5, description="Maximum number of search results to return (default: 5)")


class WebSearchTool(BaseTool[SearchProvider]):
    """Tool that queries the web via DuckDuckGo and returns structured search results."""

    name: str = "web_search"
    description: str = "Search the web for news, features, references, or repositories and get structured results."
    input_schema: Type[BaseModel] = WebSearchInput

    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Perform search query asynchronously."""
        if not self.provider:
            raise ProviderError("SearchProvider has not been assigned to this tool.")

        # Run the blocking search call in an executor to prevent event loop blocking
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            self.provider.search_text,
            query,
            max_results
        )

        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }
