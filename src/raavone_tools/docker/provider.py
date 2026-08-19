"""Docker provider implementing container and image management using the Docker SDK.

The provider is asynchronous (methods are `async`) but internally uses the
`synchronous` Docker SDK and runs operations in a thread‑pool via
`asyncio.get_running_loop().run_in_executor` to avoid blocking the event loop.
"""

import asyncio
from typing import Any, Dict, List, Optional

import docker
from docker.errors import DockerException

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import ExecutionError, ProviderError


class DockerProvider(BaseProvider):
    """Resource provider for Docker operations.

    It requires the Docker daemon to be accessible from the host where the
    agent runs. All methods perform minimal validation and raise
    ``ExecutionError`` on failure.
    """

    def __init__(self) -> None:
        # Lazily create the client when first needed.
        self._client: Optional[docker.DockerClient] = None

    async def _get_client(self) -> docker.DockerClient:
        if self._client is None:
            try:
                # Docker SDK uses environment variables to locate the daemon.
                self._client = docker.from_env()
                # Ensure we can talk to the daemon.
                await asyncio.get_running_loop().run_in_executor(None, self._client.ping)
            except DockerException as e:
                raise ProviderError(f"Unable to connect to Docker daemon: {e}") from e
        return self._client

    # ---------------------------------------------------------------------
    # Container management
    # ---------------------------------------------------------------------
    async def list_containers(self, all: bool = False) -> List[Dict[str, Any]]:
        client = await self._get_client()
        def _list():
            containers = client.containers.list(all=all)
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags,
                    "created": c.attrs.get("Created"),
                }
                for c in containers
            ]
        return await asyncio.get_running_loop().run_in_executor(None, _list)

    async def run_container(
        self,
        image: str,
        command: Optional[str] = None,
        name: Optional[str] = None,
        detach: bool = True,
        ports: Optional[Dict[str, str]] = None,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, dict]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        client = await self._get_client()
        def _run():
            try:
                container = client.containers.run(
                    image,
                    command=command,
                    name=name,
                    detach=detach,
                    ports=ports,
                    environment=environment,
                    volumes=volumes,
                    **kwargs,
                )
                return {"status": "success", "id": container.id, "name": container.name}
            except DockerException as e:
                raise ExecutionError(f"Docker run failed: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def start_container(self, container_id: str) -> Dict[str, Any]:
        client = await self._get_client()
        def _start():
            try:
                c = client.containers.get(container_id)
                c.start()
                return {"status": "success", "id": container_id}
            except DockerException as e:
                raise ExecutionError(f"Failed to start container {container_id}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _start)

    async def stop_container(self, container_id: str, timeout: int = 10) -> Dict[str, Any]:
        client = await self._get_client()
        def _stop():
            try:
                c = client.containers.get(container_id)
                c.stop(timeout=timeout)
                return {"status": "success", "id": container_id}
            except DockerException as e:
                raise ExecutionError(f"Failed to stop container {container_id}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _stop)

    async def restart_container(self, container_id: str, timeout: int = 10) -> Dict[str, Any]:
        client = await self._get_client()
        def _restart():
            try:
                c = client.containers.get(container_id)
                c.restart(timeout=timeout)
                return {"status": "success", "id": container_id}
            except DockerException as e:
                raise ExecutionError(f"Failed to restart container {container_id}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _restart)

    async def remove_container(self, container_id: str, force: bool = False) -> Dict[str, Any]:
        client = await self._get_client()
        def _remove():
            try:
                c = client.containers.get(container_id)
                c.remove(force=force)
                return {"status": "success", "id": container_id}
            except DockerException as e:
                raise ExecutionError(f"Failed to remove container {container_id}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _remove)

    async def inspect_container(self, container_id: str) -> Dict[str, Any]:
        client = await self._get_client()
        def _inspect():
            try:
                c = client.containers.get(container_id)
                return {"status": "success", "details": c.attrs}
            except DockerException as e:
                raise ExecutionError(f"Failed to inspect container {container_id}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _inspect)

    async def container_logs(self, container_id: str, tail: int = 100) -> Dict[str, Any]:
        client = await self._get_client()
        def _logs():
            try:
                c = client.containers.get(container_id)
                logs = c.logs(tail=tail).decode("utf-8", errors="replace")
                return {"status": "success", "logs": logs}
            except DockerException as e:
                raise ExecutionError(f"Failed to fetch logs for {container_id}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _logs)

    # ---------------------------------------------------------------------
    # Image management
    # ---------------------------------------------------------------------
    async def list_images(self) -> List[Dict[str, Any]]:
        client = await self._get_client()
        def _list_images():
            imgs = client.images.list()
            return [
                {
                    "id": i.id,
                    "tags": i.tags,
                    "size": i.attrs.get("Size"),
                    "created": i.attrs.get("Created"),
                }
                for i in imgs
            ]
        return await asyncio.get_running_loop().run_in_executor(None, _list_images)

    async def pull_image(self, repository: str, tag: str = "latest") -> Dict[str, Any]:
        client = await self._get_client()
        def _pull():
            try:
                image = client.images.pull(repository, tag=tag)
                return {"status": "success", "id": image.id, "tags": image.tags}
            except DockerException as e:
                raise ExecutionError(f"Failed to pull image {repository}:{tag}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _pull)

    async def remove_image(self, image_id: str, force: bool = False) -> Dict[str, Any]:
        client = await self._get_client()
        def _remove():
            try:
                client.images.remove(image=image_id, force=force)
                return {"status": "success", "id": image_id}
            except DockerException as e:
                raise ExecutionError(f"Failed to remove image {image_id}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _remove)

    # ---------------------------------------------------------------------
    # Compose helpers (very thin wrappers around ``docker compose`` CLI)
    # ---------------------------------------------------------------------
    async def compose_up(self, compose_file: str, detach: bool = True, build: bool = False, services: Optional[List[str]] = None) -> Dict[str, Any]:
        # We purposefully use the CLI because the SDK does not expose full compose API.
        import subprocess
        cmd = ["docker", "compose", "-f", compose_file, "up"]
        if detach:
            cmd.append("-d")
        if build:
            cmd.append("--build")
        if services:
            cmd.extend(services)
        def _run():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return {"status": "success", "output": result.stdout}
            except subprocess.CalledProcessError as e:
                raise ExecutionError(f"docker compose up failed: {e.stderr}")
        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def compose_down(self, compose_file: str, services: Optional[List[str]] = None) -> Dict[str, Any]:
        import subprocess
        cmd = ["docker", "compose", "-f", compose_file, "down"]
        if services:
            cmd.extend(services)
        def _run():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return {"status": "success", "output": result.stdout}
            except subprocess.CalledProcessError as e:
                raise ExecutionError(f"docker compose down failed: {e.stderr}")
        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def compose_ps(self, compose_file: str) -> Dict[str, Any]:
        import subprocess
        cmd = ["docker", "compose", "-f", compose_file, "ps", "-a", "--format", "json"]
        def _run():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                # The output is JSON lines; we simply return raw text.
                return {"status": "success", "output": result.stdout}
            except subprocess.CalledProcessError as e:
                raise ExecutionError(f"docker compose ps failed: {e.stderr}")
        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def compose_logs(self, compose_file: str, services: Optional[List[str]] = None, tail: int = 100) -> Dict[str, Any]:
        import subprocess
        cmd = ["docker", "compose", "-f", compose_file, "logs", f"--tail={tail}"]
        if services:
            cmd.extend(services)
        def _run():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return {"status": "success", "logs": result.stdout}
            except subprocess.CalledProcessError as e:
                raise ExecutionError(f"docker compose logs failed: {e.stderr}")
        return await asyncio.get_running_loop().run_in_executor(None, _run)

    # ---------------------------------------------------------------------
    # Stats (container‑level)
    # ---------------------------------------------------------------------
    async def stats(self, container_id: str) -> Dict[str, Any]:
        client = await self._get_client()
        def _stats():
            try:
                c = client.containers.get(container_id)
                # stats(stream=False) returns a dict with CPU, memory, etc.
                raw = c.stats(stream=False)
                return {"status": "success", "stats": raw}
            except DockerException as e:
                raise ExecutionError(f"Failed to get stats for {container_id}: {e}")
        return await asyncio.get_running_loop().run_in_executor(None, _stats)

    async def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            finally:
                self._client = None
