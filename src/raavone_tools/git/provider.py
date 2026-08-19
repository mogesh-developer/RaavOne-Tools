"""Git provider managing Git commands within workspace safety boundaries."""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, Optional

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import SecurityValidationError


class GitProvider(BaseProvider):
    """Resource provider that executes git commands securely inside the workspace root."""

    def __init__(self, workspace_root: Union[str, Path]) -> None:
        """Initialize the provider with a target workspace root."""
        self.workspace_root = Path(workspace_root).resolve()

    async def initialize(self) -> None:
        """Ensure workspace directory exists."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """No teardown needed for git provider."""
        pass

    def validate_path(self, target_path: Union[str, Path]) -> Path:
        """Resolve the given path and verify it is strictly within the workspace_root."""
        path_obj = Path(target_path)
        
        # If the path is relative, resolve it relative to the workspace root
        if not path_obj.is_absolute():
            resolved = (self.workspace_root / path_obj).resolve()
        else:
            resolved = path_obj.resolve()

        # Verify that resolved path begins with the workspace root path
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as e:
            raise SecurityValidationError(
                f"Security Validation Error: Path '{target_path}' lies outside "
                f"workspace boundary '{self.workspace_root}'."
            ) from e

        return resolved

    async def run_git_command(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Execute a git command asynchronously in the workspace root or specified cwd."""
        exec_cwd = cwd if cwd else self.workspace_root
        
        cmd = ["git"] + args
        
        # If on Windows, we need to handle paths correctly
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(exec_cwd)
        )
        
        stdout_bytes, stderr_bytes = await process.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
        
        return process.returncode, stdout, stderr

    async def init_repo(self, bare: bool = False) -> Tuple[int, str, str]:
        """Initialize a new git repository in the workspace. If `bare` is True, create a bare repo."""
        args = ["init"]
        if bare:
            args.append("--bare")
        return await self.run_git_command(args)

    async def fetch(self, remote: str = "origin") -> Tuple[int, str, str]:
        """Fetch updates from the specified remote."""
        return await self.run_git_command(["fetch", remote])

    async def restore(self, path: str) -> Tuple[int, str, str]:
        """Restore a file to the state of the last commit (git restore)."""
        real_path = self.validate_path(path)
        return await self.run_git_command(["restore", str(real_path)])

    async def show_commit(self, commit_hash: str) -> Tuple[int, str, str]:
        """Show details of a specific commit."""
        return await self.run_git_command(["show", commit_hash, "--pretty=fuller", "--no-patch"])

    async def list_branches(self, all_branches: bool = False) -> Tuple[int, str, str]:
        """List local (or all) branches."""
        args = ["branch"]
        if all_branches:
            args.append("-a")
        return await self.run_git_command(args)

    async def create_branch(self, name: str, start_point: str = "HEAD") -> Tuple[int, str, str]:
        """Create a new branch from start_point."""
        return await self.run_git_command(["branch", name, start_point])

    async def switch_branch(self, name: str) -> Tuple[int, str, str]:
        """Switch to the given branch (git switch)."""
        return await self.run_git_command(["switch", name])

    async def delete_branch(self, name: str, force: bool = False) -> Tuple[int, str, str]:
        """Delete a branch; if force is True, use -D."""
        args = ["branch", "-d", name]
        if force:
            args = ["branch", "-D", name]
        return await self.run_git_command(args)

    async def stash_push(self, message: str = "") -> Tuple[int, str, str]:
        """Push current changes onto stash stack."""
        args = ["stash", "push"]
        if message:
            args.extend(["-m", message])
        return await self.run_git_command(args)

    async def stash_pop(self, index: int = 0) -> Tuple[int, str, str]:
        """Pop a stash entry (default latest)."""
        return await self.run_git_command(["stash", "pop", f"stash@{{{index}}}"])

    async def stash_list(self) -> Tuple[int, str, str]:
        """List stash entries."""
        return await self.run_git_command(["stash", "list"])

    async def remote_list(self) -> Tuple[int, str, str]:
        """List configured remote repositories."""
        return await self.run_git_command(["remote", "-v"])

    async def remote_add(self, name: str, url: str) -> Tuple[int, str, str]:
        """Add a new remote with given name and URL."""
        return await self.run_git_command(["remote", "add", name, url])

    async def remote_remove(self, name: str) -> Tuple[int, str, str]:
        """Remove the remote with given name."""
        return await self.run_git_command(["remote", "remove", name])

    async def tag_list(self) -> Tuple[int, str, str]:
        """List all tags."""
        return await self.run_git_command(["tag"])

    async def tag_create(self, name: str, ref: str = "HEAD") -> Tuple[int, str, str]:
        """Create a tag at ref (default HEAD)."""
        return await self.run_git_command(["tag", name, ref])

    async def tag_delete(self, name: str) -> Tuple[int, str, str]:
        """Delete a tag by name."""
        return await self.run_git_command(["tag", "-d", name])
