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

# --- Git Init Tool ---

class GitInitInput(BaseModel):
    """Initialize a new git repository. Set `bare` to create a bare repo."""
    bare: bool = Field(default=False, description="Create a bare repository if True")

class GitInitTool(BaseTool[GitProvider]):
    """Tool to initialize a git repository in the workspace."""
    name: str = "git_init"
    description: str = "Initialize a new git repository (optionally bare) in the workspace root."
    input_schema: Type[BaseModel] = GitInitInput

    async def execute(self, bare: bool = False) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.init_repo(bare)
        if code != 0:
            raise ExecutionError(f"Git init failed: {err or out}")
        return {"status": "success", "output": out or err}

# --- Git Fetch Tool ---

class GitFetchInput(BaseModel):
    """Fetch updates from a remote. Defaults to 'origin'."""
    remote: str = Field(default="origin", description="Remote name to fetch from")

class GitFetchTool(BaseTool[GitProvider]):
    """Tool to fetch updates from a remote repository."""
    name: str = "git_fetch"
    description: str = "Fetch updates from the specified remote (default 'origin')."
    input_schema: Type[BaseModel] = GitFetchInput

    async def execute(self, remote: str = "origin") -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.fetch(remote)
        if code != 0:
            raise ExecutionError(f"Git fetch failed: {err or out}")
        return {"status": "success", "output": out or err}

# --- Git Restore Tool ---

class GitRestoreInput(BaseModel):
    """Restore a file to its last committed state."""
    path: str = Field(..., description="Path to the file to restore, relative to workspace root")

class GitRestoreTool(BaseTool[GitProvider]):
    """Tool that restores a file to the state of the last commit."""
    name: str = "git_restore"
    description: str = "Restore a file to the state of the last commit (git restore)."
    input_schema: Type[BaseModel] = GitRestoreInput

    async def execute(self, path: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.restore(path)
        if code != 0:
            raise ExecutionError(f"Git restore failed: {err or out}")
        return {"status": "success", "output": out or err}

# --- Git Show Commit Tool ---

class GitShowCommitInput(BaseModel):
    """Show details of a specific commit."""
    commit_hash: str = Field(..., description="Hash of the commit to show")

class GitShowCommitTool(BaseTool[GitProvider]):
    """Tool to display detailed information about a commit."""
    name: str = "git_show_commit"
    description: str = "Show detailed information for a specific commit hash."
    input_schema: Type[BaseModel] = GitShowCommitInput

    async def execute(self, commit_hash: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.show_commit(commit_hash)
        if code != 0:
            raise ExecutionError(f"Git show commit failed: {err or out}")
        return {"status": "success", "output": out or err}

# --- Git Branch Management Tools ---

class GitListBranchesInput(BaseModel):
    """List branches. Set `all_branches` to include remote branches."""
    all_branches: bool = Field(default=False, description="Include remote branches if True")

class GitListBranchesTool(BaseTool[GitProvider]):
    name: str = "git_list_branches"
    description: str = "List local branches (or all branches with remote) in the repository."
    input_schema: Type[BaseModel] = GitListBranchesInput

    async def execute(self, all_branches: bool = False) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.list_branches(all_branches)
        if code != 0:
            raise ExecutionError(f"Git list branches failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitCreateBranchInput(BaseModel):
    name: str = Field(..., description="Name of the new branch")
    start_point: str = Field(default="HEAD", description="Start point (commit/branch) for the new branch")

class GitCreateBranchTool(BaseTool[GitProvider]):
    name: str = "git_create_branch"
    description: str = "Create a new branch from a start point."
    input_schema: Type[BaseModel] = GitCreateBranchInput

    async def execute(self, name: str, start_point: str = "HEAD") -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.create_branch(name, start_point)
        if code != 0:
            raise ExecutionError(f"Git create branch failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitSwitchBranchInput(BaseModel):
    name: str = Field(..., description="Branch name to switch to")

class GitSwitchBranchTool(BaseTool[GitProvider]):
    name: str = "git_switch_branch"
    description: str = "Switch to an existing branch."
    input_schema: Type[BaseModel] = GitSwitchBranchInput

    async def execute(self, name: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.switch_branch(name)
        if code != 0:
            raise ExecutionError(f"Git switch branch failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitDeleteBranchInput(BaseModel):
    name: str = Field(..., description="Branch name to delete")
    force: bool = Field(default=False, description="Force delete with -D if True")

class GitDeleteBranchTool(BaseTool[GitProvider]):
    name: str = "git_delete_branch"
    description: str = "Delete a branch; use force flag for -D deletion."
    input_schema: Type[BaseModel] = GitDeleteBranchInput

    async def execute(self, name: str, force: bool = False) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.delete_branch(name, force)
        if code != 0:
            raise ExecutionError(f"Git delete branch failed: {err or out}")
        return {"status": "success", "output": out or err}

# --- Git Stash Tools ---

class GitStashPushInput(BaseModel):
    message: str = Field(default="", description="Optional stash message")

class GitStashPushTool(BaseTool[GitProvider]):
    name: str = "git_stash_push"
    description: str = "Push current changes onto the stash stack with an optional message."
    input_schema: Type[BaseModel] = GitStashPushInput

    async def execute(self, message: str = "") -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.stash_push(message)
        if code != 0:
            raise ExecutionError(f"Git stash push failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitStashPopInput(BaseModel):
    index: int = Field(default=0, description="Stash index to pop (default 0 for latest)")

class GitStashPopTool(BaseTool[GitProvider]):
    name: str = "git_stash_pop"
    description: str = "Pop a stash entry (default latest)."
    input_schema: Type[BaseModel] = GitStashPopInput

    async def execute(self, index: int = 0) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.stash_pop(index)
        if code != 0:
            raise ExecutionError(f"Git stash pop failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitStashListTool(BaseTool[GitProvider]):
    name: str = "git_stash_list"
    description: str = "List all stash entries."
    input_schema: Type[BaseModel] = BaseModel

    async def execute(self) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.stash_list()
        if code != 0:
            raise ExecutionError(f"Git stash list failed: {err or out}")
        return {"status": "success", "output": out or err}

# --- Git Remote Tools ---

class GitRemoteListTool(BaseTool[GitProvider]):
    name: str = "git_remote_list"
    description: str = "List configured remote repositories."
    input_schema: Type[BaseModel] = BaseModel

    async def execute(self) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.remote_list()
        if code != 0:
            raise ExecutionError(f"Git remote list failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitRemoteAddInput(BaseModel):
    name: str = Field(..., description="Remote name to add")
    url: str = Field(..., description="Remote URL")

class GitRemoteAddTool(BaseTool[GitProvider]):
    name: str = "git_remote_add"
    description: str = "Add a new remote repository."
    input_schema: Type[BaseModel] = GitRemoteAddInput

    async def execute(self, name: str, url: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.remote_add(name, url)
        if code != 0:
            raise ExecutionError(f"Git remote add failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitRemoteRemoveInput(BaseModel):
    name: str = Field(..., description="Remote name to remove")

class GitRemoteRemoveTool(BaseTool[GitProvider]):
    name: str = "git_remote_remove"
    description: str = "Remove an existing remote repository."
    input_schema: Type[BaseModel] = GitRemoteRemoveInput

    async def execute(self, name: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.remote_remove(name)
        if code != 0:
            raise ExecutionError(f"Git remote remove failed: {err or out}")
        return {"status": "success", "output": out or err}

# --- Git Tag Tools ---

class GitTagListTool(BaseTool[GitProvider]):
    name: str = "git_tag_list"
    description: str = "List all tags in the repository."
    input_schema: Type[BaseModel] = BaseModel

    async def execute(self) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.tag_list()
        if code != 0:
            raise ExecutionError(f"Git tag list failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitTagCreateInput(BaseModel):
    name: str = Field(..., description="Tag name to create")
    ref: str = Field(default="HEAD", description="Reference (commit) for the tag")

class GitTagCreateTool(BaseTool[GitProvider]):
    name: str = "git_tag_create"
    description: str = "Create a new tag at a given reference."
    input_schema: Type[BaseModel] = GitTagCreateInput

    async def execute(self, name: str, ref: str = "HEAD") -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.tag_create(name, ref)
        if code != 0:
            raise ExecutionError(f"Git tag create failed: {err or out}")
        return {"status": "success", "output": out or err}

class GitTagDeleteInput(BaseModel):
    name: str = Field(..., description="Tag name to delete")

class GitTagDeleteTool(BaseTool[GitProvider]):
    name: str = "git_tag_delete"
    description: str = "Delete a tag by name."
    input_schema: Type[BaseModel] = GitTagDeleteInput

    async def execute(self, name: str) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("GitProvider has not been assigned to this tool.")
        code, out, err = await self.provider.tag_delete(name)
        if code != 0:
            raise ExecutionError(f"Git tag delete failed: {err or out}")
        return {"status": "success", "output": out or err}

# End of Git tool extensions
