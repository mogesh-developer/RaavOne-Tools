import pytest
from unittest.mock import MagicMock, patch

from raavone_tools.manager import ToolManager
from raavone_tools.docker.provider import DockerProvider
from raavone_tools.docker.tool import (
    DockerListContainersTool,
    DockerStartContainerTool,
    DockerStopContainerTool,
    DockerRestartContainerTool,
    DockerContainerLogsTool,
    DockerListImagesTool,
)
from raavone_tools.exceptions import ProviderError, ExecutionError


@pytest.mark.asyncio
async def test_docker_workflow_mocked():
    # Set up mocks
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    
    # Mock container
    mock_container = MagicMock()
    mock_container.short_id = "abc1234"
    mock_container.name = "web_app"
    mock_container.image.tags = ["nginx:latest"]
    mock_container.status = "running"
    mock_container.ports = {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]}
    mock_container.logs.return_value = b"Starting NGINX web server...\nServer running."
    
    mock_client.containers.list.return_value = [mock_container]
    mock_client.containers.get.return_value = mock_container
    
    # Mock image
    mock_image = MagicMock()
    mock_image.short_id = "sha256:def5678"
    mock_image.tags = ["nginx:latest"]
    mock_image.attrs = {"Size": 150000000}
    
    mock_client.images.list.return_value = [mock_image]

    # Patch from_env to return our mock client
    with patch("docker.from_env", return_value=mock_client):
        manager = ToolManager()
        provider = DockerProvider()
        
        manager.register_tool(DockerListContainersTool(provider=provider))
        manager.register_tool(DockerStartContainerTool(provider=provider))
        manager.register_tool(DockerStopContainerTool(provider=provider))
        manager.register_tool(DockerRestartContainerTool(provider=provider))
        manager.register_tool(DockerContainerLogsTool(provider=provider))
        manager.register_tool(DockerListImagesTool(provider=provider))
        
        await manager.initialize_providers()
        
        try:
            # 1. Test List Containers
            res_list = await manager.execute("docker_list_containers", {"all_containers": True})
            assert res_list["status"] == "success"
            assert res_list["count"] == 1
            assert res_list["containers"][0]["name"] == "web_app"
            assert res_list["containers"][0]["status"] == "running"
            
            # 2. Test Start Container
            mock_container.status = "running"
            res_start = await manager.execute("docker_start", {"container_id_or_name": "web_app"})
            assert res_start["status"] == "success"
            assert res_start["current_status"] == "running"
            mock_container.start.assert_called_once()
            
            # 3. Test Stop Container
            mock_container.status = "exited"
            res_stop = await manager.execute("docker_stop", {"container_id_or_name": "web_app", "timeout": 5})
            assert res_stop["status"] == "success"
            assert res_stop["current_status"] == "exited"
            mock_container.stop.assert_called_once_with(timeout=5)
            
            # 4. Test Restart Container
            mock_container.status = "running"
            res_restart = await manager.execute("docker_restart", {"container_id_or_name": "web_app", "timeout": 5})
            assert res_restart["status"] == "success"
            assert res_restart["current_status"] == "running"
            mock_container.restart.assert_called_once_with(timeout=5)
            
            # 5. Test Logs Container
            res_logs = await manager.execute("docker_logs", {"container_id_or_name": "web_app", "tail": 10})
            assert res_logs["status"] == "success"
            assert "Starting NGINX web server..." in res_logs["logs"]
            mock_container.logs.assert_called_once_with(tail=10, stdout=True, stderr=True)
            
            # 6. Test List Images
            res_images = await manager.execute("docker_list_images", {})
            assert res_images["status"] == "success"
            assert res_images["count"] == 1
            assert res_images["images"][0]["tags"] == ["nginx:latest"]
            
        finally:
            await manager.close_providers()


@pytest.mark.asyncio
async def test_docker_offline_provider():
    # Mock connection failure
    with patch("docker.from_env", side_effect=Exception("Connection refused")):
        manager = ToolManager()
        provider = DockerProvider()
        manager.register_tool(DockerListImagesTool(provider=provider))
        
        await manager.initialize_providers()
        
        try:
            with pytest.raises(ExecutionError) as exc_info:
                await manager.execute("docker_list_images", {})
            assert "Docker client is not initialized" in str(exc_info.value)
        finally:
            await manager.close_providers()
