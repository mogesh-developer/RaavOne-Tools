"""Docker management tools."""

import asyncio
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.docker.provider import DockerProvider


# --- Docker List Containers Tool ---

class DockerListContainersInput(BaseModel):
    """Input parameters for listing containers."""
    all_containers: bool = Field(default=False, description="Whether to show all containers (True) or only running ones (False)")


class DockerListContainersTool(BaseTool[DockerProvider]):
    """Tool that lists system docker containers."""

    name: str = "docker_list_containers"
    description: str = "List docker containers with status, image, and port mappings."
    input_schema: Type[BaseModel] = DockerListContainersInput

    async def execute(self, all_containers: bool = False) -> Dict[str, Any]:
        """Query Docker client for container lists."""
        if not self.provider:
            raise ProviderError("Docker provider has not been assigned to this tool.")

        client = self.provider.get_client()
        loop = asyncio.get_running_loop()

        def _list_sync():
            containers = client.containers.list(all=all_containers)
            results = []
            for c in containers:
                results.append({
                    "id": c.short_id,
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                    "status": c.status,
                    "ports": c.ports
                })
            return results

        try:
            container_list = await loop.run_in_executor(None, _list_sync)
            return {
                "status": "success",
                "containers": container_list,
                "count": len(container_list)
            }
        except Exception as e:
            raise ExecutionError(f"Failed to list containers: {e}") from e


# --- Docker Start Container Tool ---

class DockerContainerActionInput(BaseModel):
    """Input parameters to select a target container."""
    container_id_or_name: str = Field(..., description="The ID or Name of the target docker container")


class DockerStartContainerTool(BaseTool[DockerProvider]):
    """Tool that starts a stopped docker container."""

    name: str = "docker_start"
    description: str = "Start a stopped docker container."
    input_schema: Type[BaseModel] = DockerContainerActionInput

    async def execute(self, container_id_or_name: str) -> Dict[str, Any]:
        """Start container via thread executor."""
        if not self.provider:
            raise ProviderError("Docker provider has not been assigned to this tool.")

        client = self.provider.get_client()
        loop = asyncio.get_running_loop()

        def _start_sync():
            container = client.containers.get(container_id_or_name)
            container.start()
            container.reload()
            return container.status

        try:
            status = await loop.run_in_executor(None, _start_sync)
            return {
                "status": "success",
                "container": container_id_or_name,
                "action": "start",
                "current_status": status
            }
        except Exception as e:
            raise ExecutionError(f"Failed to start container '{container_id_or_name}': {e}") from e


# --- Docker Stop Container Tool ---

class DockerStopInput(BaseModel):
    """Input parameters for stopping a container."""
    container_id_or_name: str = Field(..., description="The ID or Name of the target docker container")
    timeout: int = Field(default=10, description="Seconds to wait before killing the container")


class DockerStopContainerTool(BaseTool[DockerProvider]):
    """Tool that stops a running docker container."""

    name: str = "docker_stop"
    description: str = "Stop a running docker container."
    input_schema: Type[BaseModel] = DockerStopInput

    async def execute(self, container_id_or_name: str, timeout: int = 10) -> Dict[str, Any]:
        """Stop container via thread executor."""
        if not self.provider:
            raise ProviderError("Docker provider has not been assigned to this tool.")

        client = self.provider.get_client()
        loop = asyncio.get_running_loop()

        def _stop_sync():
            container = client.containers.get(container_id_or_name)
            container.stop(timeout=timeout)
            container.reload()
            return container.status

        try:
            status = await loop.run_in_executor(None, _stop_sync)
            return {
                "status": "success",
                "container": container_id_or_name,
                "action": "stop",
                "current_status": status
            }
        except Exception as e:
            raise ExecutionError(f"Failed to stop container '{container_id_or_name}': {e}") from e


# --- Docker Restart Container Tool ---

class DockerRestartInput(BaseModel):
    """Input parameters for restarting a container."""
    container_id_or_name: str = Field(..., description="The ID or Name of the target docker container")
    timeout: int = Field(default=10, description="Seconds to wait before killing the container during restart")


class DockerRestartContainerTool(BaseTool[DockerProvider]):
    """Tool that restarts a docker container."""

    name: str = "docker_restart"
    description: str = "Restart a docker container."
    input_schema: Type[BaseModel] = DockerRestartInput

    async def execute(self, container_id_or_name: str, timeout: int = 10) -> Dict[str, Any]:
        """Restart container via thread executor."""
        if not self.provider:
            raise ProviderError("Docker provider has not been assigned to this tool.")

        client = self.provider.get_client()
        loop = asyncio.get_running_loop()

        def _restart_sync():
            container = client.containers.get(container_id_or_name)
            container.restart(timeout=timeout)
            container.reload()
            return container.status

        try:
            status = await loop.run_in_executor(None, _restart_sync)
            return {
                "status": "success",
                "container": container_id_or_name,
                "action": "restart",
                "current_status": status
            }
        except Exception as e:
            raise ExecutionError(f"Failed to restart container '{container_id_or_name}': {e}") from e


# --- Docker Container Logs Tool ---

class DockerLogsInput(BaseModel):
    """Input parameters for logs."""
    container_id_or_name: str = Field(..., description="The ID or Name of the target docker container")
    tail: int = Field(default=100, description="Number of lines to show from the end of the logs")


class DockerContainerLogsTool(BaseTool[DockerProvider]):
    """Tool that fetches logs from a docker container."""

    name: str = "docker_logs"
    description: str = "Retrieve logs output from a docker container."
    input_schema: Type[BaseModel] = DockerLogsInput

    async def execute(self, container_id_or_name: str, tail: int = 100) -> Dict[str, Any]:
        """Fetch logs via thread executor."""
        if not self.provider:
            raise ProviderError("Docker provider has not been assigned to this tool.")

        client = self.provider.get_client()
        loop = asyncio.get_running_loop()

        def _logs_sync():
            container = client.containers.get(container_id_or_name)
            log_bytes = container.logs(tail=tail, stdout=True, stderr=True)
            return log_bytes.decode("utf-8", errors="replace")

        try:
            logs = await loop.run_in_executor(None, _logs_sync)
            return {
                "status": "success",
                "container": container_id_or_name,
                "logs": logs
            }
        except Exception as e:
            raise ExecutionError(f"Failed to retrieve logs for '{container_id_or_name}': {e}") from e


# --- Docker List Images Tool ---

class DockerListImagesInput(BaseModel):
    """Input parameters for images (empty schema)."""
    pass


class DockerListImagesTool(BaseTool[DockerProvider]):
    """Tool that lists system docker images."""

    name: str = "docker_list_images"
    description: str = "List all local docker images."
    input_schema: Type[BaseModel] = DockerListImagesInput

    async def execute(self) -> Dict[str, Any]:
        """Query local images list."""
        if not self.provider:
            raise ProviderError("Docker provider has not been assigned to this tool.")

        client = self.provider.get_client()
        loop = asyncio.get_running_loop()

        def _images_sync():
            images = client.images.list()
            results = []
            for img in images:
                results.append({
                    "id": img.short_id,
                    "tags": img.tags,
                    "size": img.attrs.get("Size") if img.attrs else 0
                })
            return results

        try:
            image_list = await loop.run_in_executor(None, _images_sync)
            return {
                "status": "success",
                "images": image_list,
                "count": len(image_list)
            }
        except Exception as e:
            raise ExecutionError(f"Failed to list local docker images: {e}") from e
