"""Git execution tools."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError, SecurityValidationError
from raavone_tools.git.provider import GitProvider


# --- Git Status Tool ---

class GitStatusInput(BaseModel):
    """Input parameters for git status."""
    pass


class GitStatusTool(BaseTool[GitProvider]):
    """Tool that returns the structured status of the workspace Git repository."""

    name: str = "git_status"
    description: str = "Get the current git branch and list of staged, modified, untracked, and deleted files."
    input_schema: Type[BaseModel] = GitStatusInput

    async def execute(self) -> Dict[str, Any]:
        """Query status and parse into a structured dictionary."""
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")

        # 1. Get current branch
        code_branch, out_branch, err_branch = await self.provider.run_git_command(["branch", "--show-current"])
        if code_branch != 0:
            raise ExecutionError(f"Failed to fetch branch status: {err_branch or out_branch}")

        # 2. Get status porcelain output
        code_status, out_status, err_status = await self.provider.run_git_command(["status", "--porcelain"])
        if code_status != 0:
            raise ExecutionError(f"Failed to fetch git status: {err_status or out_status}")

        modified = []
        staged = []
        untracked = []
        deleted = []

        if out_status:
            for line in out_status.splitlines():
                if len(line) < 4:
                    continue
                status_code = line[:2]
                file_path = line[3:].strip()
                
                # Strip quotes if filename contains spaces/special characters
                if file_path.startswith('"') and file_path.endswith('"'):
                    file_path = file_path[1:-1]

                # Status codes mapping
                # X (staged status), Y (unstaged status)
                x, y = status_code[0], status_code[1]

                if x in ("M", "A", "R", "D", "C"):
                    staged.append(file_path)
                
                if y == "M":
                    modified.append(file_path)
                elif y == "D":
                    deleted.append(file_path)
                elif x == "?" and y == "?":
                    untracked.append(file_path)

        return {
            "status": "success",
            "branch": out_branch,
            "modified": modified,
            "staged": staged,
            "untracked": untracked,
            "deleted": deleted,
        }


# --- Git Clone Tool ---

class GitCloneInput(BaseModel):
    """Input parameters for cloning a repository."""
    repo_url: str = Field(..., description="The HTTPS or SSH Git URL of the repository to clone")
    dest_dir: Optional[str] = Field(None, description="Optional destination folder path inside the workspace")


class GitCloneTool(BaseTool[GitProvider]):
    """Tool that clones a remote repository into the workspace root."""

    name: str = "git_clone"
    description: str = "Clone a remote Git repository."
    input_schema: Type[BaseModel] = GitCloneInput

    async def execute(self, repo_url: str, dest_dir: Optional[str] = None) -> Dict[str, Any]:
        """Clone the repository."""
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")

        args = ["clone", repo_url]
        if dest_dir:
            dest_real = self.provider.validate_path(dest_dir)
            args.append(str(dest_real))
            
        code, out, err = await self.provider.run_git_command(args)
        if code != 0:
            raise ExecutionError(f"Git clone failed: {err or out}")

        return {
            "status": "success",
            "message": f"Successfully cloned '{repo_url}'",
            "output": out or err
        }


# --- Git Pull Tool ---

class GitPullInput(BaseModel):
    """Input parameters for git pull."""
    pass


class GitPullTool(BaseTool[GitProvider]):
    """Tool that pulls updates from the remote repository."""

    name: str = "git_pull"
    description: str = "Pull updates from the remote repository branch."
    input_schema: Type[BaseModel] = GitPullInput

    async def execute(self) -> Dict[str, Any]:
        """Pull updates."""
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")

        code, out, err = await self.provider.run_git_command(["pull"])
        if code != 0:
            raise ExecutionError(f"Git pull failed: {err or out}")

        return {
            "status": "success",
            "output": out or err
        }


# --- Git Add Tool ---

class GitAddInput(BaseModel):
    """Input parameters for git add."""
    files: List[str] = Field(default=["."], description="List of filepaths relative to workspace root to stage. Defaults to ['.']")


class GitAddTool(BaseTool[GitProvider]):
    """Tool that stages files for the next commit."""

    name: str = "git_add"
    description: str = "Stage changes in one or more files."
    input_schema: Type[BaseModel] = GitAddInput

    async def execute(self, files: List[str]) -> Dict[str, Any]:
        """Add files to git staging."""
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")

        # Validate all file paths before staging
        validated_files = []
        for file in files:
            if file == ".":
                validated_files.append(".")
            else:
                real_file = self.provider.validate_path(file)
                validated_files.append(str(real_file))

        code, out, err = await self.provider.run_git_command(["add"] + validated_files)
        if code != 0:
            raise ExecutionError(f"Git add failed: {err or out}")

        return {
            "status": "success",
            "message": f"Staged {len(files)} files: {', '.join(files)}"
        }


# --- Git Commit Tool ---

class GitCommitInput(BaseModel):
    """Input parameters for git commit."""
    message: str = Field(..., description="Commit message describing the changes")


class GitCommitTool(BaseTool[GitProvider]):
    """Tool that commits staged changes to the repository."""

    name: str = "git_commit"
    description: str = "Commit staged changes to the repository with a commit message."
    input_schema: Type[BaseModel] = GitCommitInput

    async def execute(self, message: str) -> Dict[str, Any]:
        """Commit staged changes."""
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")

        code, out, err = await self.provider.run_git_command(["commit", "-m", message])
        if code != 0:
            raise ExecutionError(f"Git commit failed: {err or out}")

        return {
            "status": "success",
            "output": out or err
        }


# --- Git Push Tool ---

class GitPushInput(BaseModel):
    """Input parameters for git push."""
    remote: str = Field(default="origin", description="Name of the remote repository (defaults to 'origin')")
    branch: Optional[str] = Field(None, description="Optional branch name to push to")


class GitPushTool(BaseTool[GitProvider]):
    """Tool that pushes committed changes to a remote repository."""

    name: str = "git_push"
    description: str = "Push local commits to the remote repository."
    input_schema: Type[BaseModel] = GitPushInput

    async def execute(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Push changes."""
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")

        args = ["push", remote]
        if branch:
            args.append(branch)

        code, out, err = await self.provider.run_git_command(args)
        if code != 0:
            raise ExecutionError(f"Git push failed: {err or out}")

        return {
            "status": "success",
            "output": out or err
        }


# --- Git Log Tool ---

class GitLogInput(BaseModel):
    """Input parameters for git log."""
    limit: int = Field(default=10, description="Max number of commit history items to retrieve (default: 10)")


class GitLogTool(BaseTool[GitProvider]):
    """Tool that returns structured commit history log."""

    name: str = "git_log"
    description: str = "Get structured local git commit log history."
    input_schema: Type[BaseModel] = GitLogInput

    async def execute(self, limit: int = 10) -> Dict[str, Any]:
        """Fetch log and parse each commit into a dictionary."""
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")

        code, out, err = await self.provider.run_git_command([
            "log",
            f"-n", str(limit),
            '--pretty=format:%H|%an|%ad|%s',
            '--date=short'
        ])
        if code != 0:
            raise ExecutionError(f"Git log failed: {err or out}")

        commits = []
        if out:
            for line in out.splitlines():
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3]
                    })

        return {
            "status": "success",
            "commits": commits,
            "count": len(commits)
        }


# --- Git Diff Tool ---

class GitDiffInput(BaseModel):
    """Input parameters for git diff."""
    file_path: Optional[str] = Field(None, description="Optional path to a file to diff")
    staged: bool = Field(default=False, description="Set to True to show staged changes (equivalent to --cached)")


class GitDiffTool(BaseTool[GitProvider]):
    """Tool that returns diff updates from unstaged or staged changes."""

    name: str = "git_diff"
    description: str = "View unstaged or staged code diff changes."
    input_schema: Type[BaseModel] = GitDiffInput

    async def execute(self, file_path: Optional[str] = None, staged: bool = False) -> Dict[str, Any]:
        """Query diff."""
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")

        args = ["diff"]
        if staged:
            args.append("--cached")
        if file_path:
            real_file = self.provider.validate_path(file_path)
            args.append(str(real_file))

        code, out, err = await self.provider.run_git_command(args)
        if code != 0:
            raise ExecutionError(f"Git diff failed: {err or out}")

        return {
            "status": "success",
            "diff": out
        }
