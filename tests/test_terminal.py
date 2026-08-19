import pytest
import tempfile
from pathlib import Path
from raavone_tools.manager import ToolManager
from raavone_tools.terminal.provider import TerminalProvider
from raavone_tools.terminal.tool import RunCommandTool, WhichTool
from raavone_tools.exceptions import ExecutionError

@pytest.mark.asyncio
async def test_terminal_tools():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        manager = ToolManager()
        provider = TerminalProvider(workspace_root=workspace)
        manager.register_tool(RunCommandTool(provider=provider))
        manager.register_tool(WhichTool(provider=provider))
        await manager.initialize_providers()

        # Basic command execution
        run_result = await manager.execute(
            "run_command",
            {"command": "echo hello terminal"}
        )
        assert run_result["status"] in ("success", "completed")
        assert run_result["exit_code"] == 0
        assert "hello terminal" in run_result["stdout"]
        assert "duration" in run_result

        # Working directory is respected (legacy working_dir alias)
        wd_result = await manager.execute(
            "run_command",
            {"command": "echo test > out.txt", "working_dir": "."}
        )
        assert wd_result["status"] in ("success", "completed")
        assert wd_result["exit_code"] == 0
        assert (workspace / "out.txt").exists()

        # cwd is respected
        sub = workspace / "subdir"
        sub.mkdir()
        cd_result = await manager.execute(
            "run_command",
            {"command": "echo test > cwd_test.txt", "cwd": "subdir"}
        )
        assert cd_result["exit_code"] == 0
        assert (sub / "cwd_test.txt").exists()

        # Non-zero exit codes are captured
        exit_result = await manager.execute(
            "run_command",
            {"command": "python -c \"import sys; sys.exit(3)\""}
        )
        assert exit_result["exit_code"] == 3
        assert exit_result["status"] == "completed"

        # Environment variables are passed through
        env_result = await manager.execute(
            "run_command",
            {
                "command": "python -c \"import os; print(os.environ.get('MY_VAR', ''))\"",
                "env": {"MY_VAR": "custom-env-value"},
            }
        )
        assert "custom-env-value" in env_result["stdout"]

        # Secret values are redacted from output
        secret_result = await manager.execute(
            "run_command",
            {
                "command": "python -c \"import os; print(os.environ.get('API_TOKEN', ''))\"",
                "env": {"API_TOKEN": "super_secret_123"},
            }
        )
        assert "super_secret_123" not in secret_result["stdout"]
        assert "***" in secret_result["stdout"]

        # stdin is forwarded to the command
        stdin_result = await manager.execute(
            "run_command",
            {
                "command": "python -c \"import sys; print(sys.stdin.read())\"",
                "stdin": "piped stdin data",
            }
        )
        assert "piped stdin data" in stdin_result["stdout"]

        # Output size limit is enforced
        limited = await manager.execute(
            "run_command",
            {
                "command": "python -c \"print('x' * 100)\"",
                "max_output_chars": 10,
            }
        )
        assert limited["stdout_truncated"] is True
        assert len(limited["stdout"]) == 10

        # Timeout kills a hanging command
        with pytest.raises(ExecutionError) as timeout_exc:
            await manager.execute(
                "run_command",
                {"command": "python -c \"import time; time.sleep(30)\"", "timeout": 1},
            )
        assert "timed out" in str(timeout_exc.value)

        # Dangerous command policy blocks destructive commands
        with pytest.raises(ExecutionError) as danger_exc:
            await manager.execute("run_command", {"command": "rm -rf /"})
        assert "Security Validation Error" in str(danger_exc.value)

        # allow_dangerous overrides the policy (command still fails to find rm on win, but not blocked by policy)
        override = await manager.execute(
            "run_command",
            {"command": "python -c \"import sys; sys.exit(0)\"", "allow_dangerous": True},
        )
        assert override["exit_code"] == 0

        # Security check: working directory outside workspace
        with pytest.raises(ExecutionError) as exc_info:
            await manager.execute(
                "run_command",
                {"command": "echo hack", "working_dir": "../outside"}
            )
        assert "Security Validation Error" in str(exc_info.value)

        # which tool
        which_result = await manager.execute("which", {"command": "python"})
        assert which_result["status"] == "success"
        assert which_result["found"] is True
        assert which_result["path"]

        missing_result = await manager.execute("which", {"command": "definitely-not-a-real-bin-xyz"})
        assert missing_result["found"] is False
        assert missing_result["path"] is None