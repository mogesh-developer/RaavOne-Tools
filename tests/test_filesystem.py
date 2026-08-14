import pytest
import tempfile
from pathlib import Path
from raavone_tools.manager import ToolManager
from raavone_tools.filesystem.provider import FilesystemProvider
from raavone_tools.filesystem.tool import ReadFileTool, WriteFileTool, ListDirTool
from raavone_tools.exceptions import ExecutionError

@pytest.mark.asyncio
async def test_filesystem_tools():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        manager = ToolManager()
        provider = FilesystemProvider(workspace_root=workspace)
        await manager.initialize_providers()

        # Register tools
        manager.register_tool(WriteFileTool(provider=provider))
        manager.register_tool(ReadFileTool(provider=provider))
        manager.register_tool(ListDirTool(provider=provider))

        # Write file
        write_result = await manager.execute(
            "write_file",
            {"path": "test.txt", "content": "Hello World"}
        )
        assert write_result["status"] == "success"
        assert write_result["bytes_written"] == 11

        # Read file
        read_result = await manager.execute(
            "read_file",
            {"path": "test.txt"}
        )
        assert read_result["status"] == "success"
        assert read_result["content"] == "Hello World"

        # List directory
        list_result = await manager.execute("list_dir", {"path": "."})
        assert list_result["status"] == "success"
        items = list_result["items"]
        assert len(items) == 1
        assert items[0]["name"] == "test.txt"
        assert items[0]["type"] == "file"

        # Security check: try to write outside workspace
        with pytest.raises(ExecutionError) as exc_info:
            await manager.execute(
                "write_file",
                {"path": "../outside.txt", "content": "hack"}
            )
        assert "Security Validation Error" in str(exc_info.value)
