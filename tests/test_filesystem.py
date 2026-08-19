import pytest
import tempfile
from pathlib import Path
from raavone_tools.manager import ToolManager
from raavone_tools.filesystem.provider import FilesystemProvider
from raavone_tools.filesystem.tool import (
    ReadFileTool,
    WriteFileTool,
    ListDirTool,
    DeleteFileTool,
    CreateDirTool,
    CopyTool,
    MoveTool,
    ExistsTool,
    FileInfoTool,
    SearchTool,
)
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


@pytest.mark.asyncio
async def test_filesystem_extended_tools():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        manager = ToolManager()
        provider = FilesystemProvider(workspace_root=workspace)
        manager.register_tool(WriteFileTool(provider=provider))
        manager.register_tool(ReadFileTool(provider=provider))
        manager.register_tool(ListDirTool(provider=provider))
        manager.register_tool(DeleteFileTool(provider=provider))
        manager.register_tool(CreateDirTool(provider=provider))
        manager.register_tool(CopyTool(provider=provider))
        manager.register_tool(MoveTool(provider=provider))
        manager.register_tool(ExistsTool(provider=provider))
        manager.register_tool(FileInfoTool(provider=provider))
        manager.register_tool(SearchTool(provider=provider))
        await manager.initialize_providers()

        # create_dir
        res = await manager.execute("create_dir", {"path": "reports"})
        assert res["status"] == "success"
        assert (workspace / "reports").is_dir()

        # exists (dir + missing)
        res = await manager.execute("exists", {"path": "reports"})
        assert res["exists"] is True
        res = await manager.execute("exists", {"path": "nope.txt"})
        assert res["exists"] is False

        # write then file_info
        await manager.execute("write_file", {"path": "reports/report.txt", "content": "hello"})
        info = await manager.execute("file_info", {"path": "reports/report.txt"})
        assert info["status"] == "success"
        assert info["name"] == "report.txt"
        assert info["size"] == 5
        assert info["type"] == "file"
        assert "modified" in info

        # copy
        res = await manager.execute("copy", {"source": "reports/report.txt", "destination": "reports/copy.txt"})
        assert res["status"] == "success"
        assert (workspace / "reports/copy.txt").read_text() == "hello"

        # move
        res = await manager.execute("move", {"source": "reports/copy.txt", "destination": "moved.txt"})
        assert res["status"] == "success"
        assert (workspace / "moved.txt").exists()
        assert not (workspace / "reports/copy.txt").exists()

        # search
        res = await manager.execute("search", {"path": ".", "pattern": "*.txt"})
        assert res["status"] == "success"
        assert "reports/report.txt" in res["results"]
        assert "moved.txt" in res["results"]

        # search recursive nested
        res = await manager.execute("search", {"path": ".", "pattern": "*.txt", "recursive": True})
        assert res["count"] == 2

        # delete_file
        res = await manager.execute("delete_file", {"path": "moved.txt"})
        assert res["status"] == "success"
        assert not (workspace / "moved.txt").exists()

        # delete missing file should raise
        with pytest.raises(ExecutionError):
            await manager.execute("delete_file", {"path": "moved.txt"})

        # Security check: delete outside workspace
        with pytest.raises(ExecutionError) as exc_info:
            await manager.execute("delete_file", {"path": "../evil.txt"})
        assert "Security Validation Error" in str(exc_info.value)

        # Security check: copy outside workspace
        with pytest.raises(ExecutionError) as exc_info:
            await manager.execute(
                "copy",
                {"source": "reports/report.txt", "destination": "../evil.txt"},
            )
        assert "Security Validation Error" in str(exc_info.value)
