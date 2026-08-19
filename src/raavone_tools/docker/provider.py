"""Docker resource provider interface."""

import docker
from typing import Any, Dict, List, Optional
from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import ProviderError, ExecutionError


class DockerProvider(BaseProvider):
    """Resource provider interface for managing Docker client contexts."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        """Initialize Docker provider with optional custom daemon base url."""
        self.base_url = base_url
        self.client = None

    async def initialize(self) -> None:
        """Initialize the Docker client connection from the environment."""
        try:
            if self.base_url:
                self.client = docker.DockerClient(base_url=self.base_url)
            else:
                self.client = docker.from_env()
            # Perform a ping to verify connection
            self.client.ping()
        except Exception as e:
            # We don't crash startup if docker daemon isn't running, but store the error.
            # If the user tries to use the tools later, they will get a descriptive ProviderError.
            self.client = None

    async def close(self) -> None:
        """Close Docker client resources."""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

    def get_client(self) -> docker.DockerClient:
        """Get the initialized client instance or raise ProviderError if unavailable."""
        if not self.client:
            raise ProviderError(
                "Docker client is not initialized or daemon is not running. "
                "Please verify that Docker Desktop/daemon is active."
            )
        return self.client
