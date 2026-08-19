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

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        follow_redirects: Optional[bool] = None,
        stream: bool = False,
    ) -> httpx.Response:
        """Generic request wrapper supporting all HTTP verbs and multipart upload.
        Parameters are passed directly to httpx.AsyncClient.request.
        """
        client = await self.get_client()
        request_kwargs: Dict[str, Any] = {
            "url": url,
            "headers": headers,
            "params": params,
            "json": json,
            "data": data,
            "files": files,
            "timeout": timeout,
            "follow_redirects": follow_redirects,
        }
        request_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}
        response = await client.request(method, **request_kwargs, stream=stream)
        response.raise_for_status()
        return response
