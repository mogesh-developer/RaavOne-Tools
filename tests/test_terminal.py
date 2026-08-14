import pytest
import tempfile
from pathlib import Path
from raavone_tools.manager import ToolManager
from raavone_tools.terminal.provider import TerminalProvider
from raavone_tools.terminal.tool import RunCommandTool
from raavone_tools.exceptions import ExecutionError

@pytest.mark.asyncio
async def test_terminal_tools():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        manager = ToolManager()
        provider = TerminalProvider(workspace_root=workspace)
        await manager.initialize_providers()

        # Register tool
        manager.register_tool(RunCommandTool(provider=provider))

        # Basic command execution
        run_result = await manager.execute(
            "run_command",
            {"command": "echo hello terminal"}
        )
        assert run_result["status"] == "success"
        assert run_result["exit_code"] == 0
        assert "hello terminal" in run_result["stdout"]

        # Working directory is respected
        wd_result = await manager.execute(
            "run_command",
            {"command": "echo test > out.txt", "working_dir": "."}
        )
        assert wd_result["status"] == "success"
        assert wd_result["exit_code"] == 0
        assert (workspace / "out.txt").exists()

        # Non-zero exit codes are captured
        exit_result = await manager.execute(
            "run_command",
            {"command": "python -c \"import sys; sys.exit(3)\""}
        )
        assert exit_result["exit_code"] == 3

        # Security check: working directory outside workspace
        with pytest.raises(ExecutionError) as exc_info:
            await manager.execute(
                "run_command",
                {"command": "echo hack", "working_dir": "../outside"}
            )
        assert "Security Validation Error" in str(exc_info.value)
