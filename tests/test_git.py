import os
import tempfile
import asyncio
import pytest
from pathlib import Path

from raavone_tools.manager import ToolManager
from raavone_tools.git.provider import GitProvider
from raavone_tools.git.tool import (
    GitStatusTool,
    GitCloneTool,
    GitPullTool,
    GitAddTool,
    GitCommitTool,
    GitPushTool,
    GitLogTool,
    GitDiffTool,
)
from raavone_tools.exceptions import SecurityValidationError, ExecutionError


@pytest.mark.asyncio
async def test_git_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        manager = ToolManager()
        provider = GitProvider(workspace_root=workspace_root)
        
        manager.register_tool(GitStatusTool(provider=provider))
        manager.register_tool(GitCloneTool(provider=provider))
        manager.register_tool(GitPullTool(provider=provider))
        manager.register_tool(GitAddTool(provider=provider))
        manager.register_tool(GitCommitTool(provider=provider))
        manager.register_tool(GitPushTool(provider=provider))
        manager.register_tool(GitLogTool(provider=provider))
        manager.register_tool(GitDiffTool(provider=provider))
        
        await manager.initialize_providers()
        
        try:
            # 1. Initialize temporary git repository
            code_init, _, _ = await provider.run_git_command(["init", "-b", "main"])
            if code_init != 0:
                # Fallback if -b is not supported on older git versions
                await provider.run_git_command(["init"])
            
            # Setup dummy git configuration for commit matching
            await provider.run_git_command(["config", "user.name", "Test User"])
            await provider.run_git_command(["config", "user.email", "test@example.com"])
            await provider.run_git_command(["config", "commit.gpgsign", "false"])

            # 2. Write a file and check git status (Untracked)
            test_file = workspace_root / "test_file.txt"
            test_file.write_text("Initial content")
            
            res_status = await manager.execute("git_status", {})
            assert res_status["status"] == "success"
            assert "test_file.txt" in res_status["untracked"]

            # 3. Test Git Add
            res_add = await manager.execute("git_add", {"files": ["test_file.txt"]})
            assert res_add["status"] == "success"
            
            # Staged status check
            res_status2 = await manager.execute("git_status", {})
            assert "test_file.txt" in res_status2["staged"]

            # 4. Test Git Commit
            res_commit = await manager.execute("git_commit", {"message": "Initial commit"})
            assert res_commit["status"] == "success"
            
            # 5. Modify file to test Git Diff and staged/unstaged
            test_file.write_text("Initial content\nModified content")
            res_diff = await manager.execute("git_diff", {"file_path": "test_file.txt"})
            assert res_diff["status"] == "success"
            assert "+Modified content" in res_diff["diff"]

            # Stage modification
            await manager.execute("git_add", {"files": ["test_file.txt"]})
            res_diff_staged = await manager.execute("git_diff", {"staged": True})
            assert "+Modified content" in res_diff_staged["diff"]

            await manager.execute("git_commit", {"message": "Second commit"})

            # 6. Test Git Log
            res_log = await manager.execute("git_log", {"limit": 5})
            assert res_log["status"] == "success"
            assert res_log["count"] == 2
            commits = res_log["commits"]
            assert commits[0]["message"] == "Second commit"
            assert commits[1]["message"] == "Initial commit"

            # 7. Security Check: path outside boundary validation
            with pytest.raises(ExecutionError) as exc_info:
                await manager.execute("git_add", {"files": ["../outside.txt"]})
            assert "Security Validation Error" in str(exc_info.value)

        finally:
            await manager.close_providers()
