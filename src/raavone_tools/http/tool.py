"""HTTP execution tools."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Type
import httpx
from pydantic import BaseModel, Field, ConfigDict

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.http.provider import HttpProvider


def _parse_response(response: httpx.Response) -> Dict[str, Any]:
    """Helper to parse a httpx response into a serializable dictionary."""
    try:
        json_data = response.json()
    except Exception:
        json_data = None

    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response.text,
        "json": json_data,
    }


# --- HTTP GET Tool ---

class HttpGetInput(BaseModel):
    """Input parameters for HTTP GET tool."""
    url: str = Field(..., description="The destination URL (must include HTTP/HTTPS protocol)")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers")
    params: Optional[Dict[str, Any]] = Field(None, description="Optional query parameters")


class HttpGetTool(BaseTool[HttpProvider]):
    """Tool that sends an HTTP GET request."""

    name: str = "http_get"
    description: str = "Perform an HTTP GET request to the specified URL."
    input_schema: Type[BaseModel] = HttpGetInput

    async def execute(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform the GET request and return the response."""
        if not self.provider:
            raise ProviderError("HttpProvider has not been assigned to this tool.")

        client = await self.provider.get_client()
        try:
            response = await client.get(url, headers=headers, params=params)
            return _parse_response(response)
        except Exception as e:
            raise ExecutionError(f"HTTP GET failed for {url}: {e}") from e


# --- HTTP POST Tool ---

class HttpPostInput(BaseModel):
    """Input parameters for HTTP POST tool."""
    model_config = ConfigDict(populate_by_name=True)

    url: str = Field(..., description="The destination URL (must include HTTP/HTTPS protocol)")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, alias="json", description="Optional JSON request body")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional form-encoded request body")


class HttpPostTool(BaseTool[HttpProvider]):
    """Tool that sends an HTTP POST request."""

    name: str = "http_post"
    description: str = "Perform an HTTP POST request to the specified URL."
    input_schema: Type[BaseModel] = HttpPostInput

    async def execute(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform the POST request and return the response."""
        if not self.provider:
            raise ProviderError("HttpProvider has not been assigned to this tool.")

        client = await self.provider.get_client()
        try:
            response = await client.post(url, headers=headers, json=json_data, data=data)
            return _parse_response(response)
        except Exception as e:
            raise ExecutionError(f"HTTP POST failed for {url}: {e}") from e


# --- HTTP PUT Tool ---

class HttpPutInput(BaseModel):
    """Input parameters for HTTP PUT tool."""
    model_config = ConfigDict(populate_by_name=True)

    url: str = Field(..., description="The destination URL (must include HTTP/HTTPS protocol)")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, alias="json", description="Optional JSON request body")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional form-encoded request body")


class HttpPutTool(BaseTool[HttpProvider]):
    """Tool that sends an HTTP PUT request."""

    name: str = "http_put"
    description: str = "Perform an HTTP PUT request to the specified URL."
    input_schema: Type[BaseModel] = HttpPutInput

    async def execute(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform the PUT request and return the response."""
        if not self.provider:
            raise ProviderError("HttpProvider has not been assigned to this tool.")

        client = await self.provider.get_client()
        try:
            response = await client.put(url, headers=headers, json=json_data, data=data)
            return _parse_response(response)
        except Exception as e:
            raise ExecutionError(f"HTTP PUT failed for {url}: {e}") from e


# --- HTTP PATCH Tool ---

class HttpPatchInput(BaseModel):
    """Input parameters for HTTP PATCH tool."""
    model_config = ConfigDict(populate_by_name=True)

    url: str = Field(..., description="The destination URL (must include HTTP/HTTPS protocol)")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers")
    json_data: Optional[Dict[str, Any]] = Field(None, alias="json", description="Optional JSON request body")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional form-encoded request body")


class HttpPatchTool(BaseTool[HttpProvider]):
    """Tool that sends an HTTP PATCH request."""

    name: str = "http_patch"
    description: str = "Perform an HTTP PATCH request to the specified URL."
    input_schema: Type[BaseModel] = HttpPatchInput

    async def execute(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform the PATCH request and return the response."""
        if not self.provider:
            raise ProviderError("HttpProvider has not been assigned to this tool.")

        client = await self.provider.get_client()
        try:
            response = await client.patch(url, headers=headers, json=json_data, data=data)
            return _parse_response(response)
        except Exception as e:
            raise ExecutionError(f"HTTP PATCH failed for {url}: {e}") from e


# --- HTTP DELETE Tool ---

class HttpDeleteInput(BaseModel):
    """Input parameters for HTTP DELETE tool."""
    url: str = Field(..., description="The destination URL (must include HTTP/HTTPS protocol)")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers")


class HttpDeleteTool(BaseTool[HttpProvider]):
    """Tool that sends an HTTP DELETE request."""

    name: str = "http_delete"
    description: str = "Perform an HTTP DELETE request to the specified URL."
    input_schema: Type[BaseModel] = HttpDeleteInput

    async def execute(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Perform the DELETE request and return the response."""
        if not self.provider:
            raise ProviderError("HttpProvider has not been assigned to this tool.")

        client = await self.provider.get_client()
        try:
            response = await client.delete(url, headers=headers)
            return _parse_response(response)
        except Exception as e:
            raise ExecutionError(f"HTTP DELETE failed for {url}: {e}") from e


# --- HTTP Download Tool ---

class HttpDownloadInput(BaseModel):
    """Input parameters for HTTP Download tool."""
    url: str = Field(..., description="The source URL of the file to download")
    dest_path: str = Field(..., description="Local filepath where the file should be saved")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers")


class HttpDownloadTool(BaseTool[HttpProvider]):
    """Tool that downloads a file from a URL to a local destination path."""

    name: str = "http_download"
    description: str = "Download a file from a URL and save it locally."
    input_schema: Type[BaseModel] = HttpDownloadInput

    async def execute(
        self,
        url: str,
        dest_path: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Download the file and save it to the destination path."""
        if not self.provider:
            raise ProviderError("HttpProvider has not been assigned to this tool.")

        client = await self.provider.get_client()
        try:
            dest = Path(dest_path)
            dest.parent.mkdir(parents=True, exist_ok=True)

            async with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "dest_path": str(dest.resolve()),
                "status": "success",
            }
        except Exception as e:
            raise ExecutionError(f"HTTP Download failed for {url}: {e}") from e
