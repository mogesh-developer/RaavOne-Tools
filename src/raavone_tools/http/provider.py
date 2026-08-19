"""HTTP provider managing httpx.AsyncClient session."""

from typing import Any, Dict, Optional
import httpx

from raavone_tools.base import BaseProvider


class HttpProvider(BaseProvider):
    """Resource provider that manages HTTP request sessions via httpx."""

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: float = 30.0) -> None:
        """Initialize the HTTP provider with optional default headers and default timeout."""
        self.default_headers = headers or {}
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize the httpx AsyncClient session."""
        if not self.client:
            self.client = httpx.AsyncClient(
                headers=self.default_headers,
                timeout=self.timeout
            )

    async def close(self) -> None:
        """Teardown and close the AsyncClient session."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get the active AsyncClient instance, initializing if necessary."""
        if not self.client:
            await self.initialize()
        return self.client
