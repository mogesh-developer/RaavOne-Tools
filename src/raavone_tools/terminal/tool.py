"""Terminal execution tools."""

from typing import Any, Dict, Optional, Type
from pydantic import AliasChoices, BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.terminal.provider import TerminalProvider


# --- Run Command Tool ---

class RunCommandInput(BaseModel):
    """Input parameters for the run command tool."""
    command: str = Field(..., description="Shell command to execute")
    cwd: Optional[str] = Field(
        None,
        description="Working directory path relative to workspace root",
        validation_alias=AliasChoices("cwd", "working_dir"),
    )
    env: Optional[Dict[str, str]] = Field(
        None,
        description="Environment variables to set for the command (secret values are redacted from output)",
    )
    timeout: int = Field(60, description="Maximum execution time in seconds")
    shell: bool = Field(True, description="Run the command through a shell")
    stdin: Optional[str] = Field(
        None,
        description="Text input to send to the command's standard input",
    )
    max_output_chars: Optional[int] = Field(
        20000,
        description="Maximum number of characters to return from stdout/stderr",
    )
    allow_dangerous: bool = Field(
        False,
        description="Allow commands matching the dangerous command policy",
    )


class RunCommandTool(BaseTool[TerminalProvider]):
    """Tool that executes a terminal command within the workspace boundary."""

    name: str = "run_command"
    description: str = (
        "Execute a shell command within the workspace and return its output, "
        "exit code, and duration."
    )
    input_schema: Type[BaseModel] = RunCommandInput

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 60,
        shell: bool = True,
        stdin: Optional[str] = None,
        max_output_chars: Optional[int] = 20000,
        allow_dangerous: bool = False,
    ) -> Dict[str, Any]:
        """Run the command and return its exit code, stdout, and stderr."""
        if not self.provider:
            raise ProviderError("TerminalProvider has not been assigned to this tool.")

        try:
            result = await self.provider.run_command(
                command,
                working_dir=cwd,
                timeout=timeout,
                shell=shell,
                env=env,
                stdin=stdin,
                max_output_chars=max_output_chars,
                allow_dangerous=allow_dangerous,
            )
            return {
                "command": command,
                "exit_code": result["exit_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "duration": result["duration"],
                "stdout_truncated": result["stdout_truncated"],
                "stderr_truncated": result["stderr_truncated"],
                "status": "success" if result["exit_code"] == 0 else "completed",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to run command '{command}': {e}") from e


# --- Which Tool ---

class WhichInput(BaseModel):
    """Input parameters for the which tool."""
    command: str = Field(..., description="Executable name to look up, e.g. 'python', 'git'")


class WhichTool(BaseTool[TerminalProvider]):
    """Tool that locates an executable on the system PATH."""

    name: str = "which"
    description: str = "Locate an executable (e.g. python, git, node) on the system PATH."
    input_schema: Type[BaseModel] = WhichInput

    async def execute(self, command: str) -> Dict[str, Any]:
        """Return the resolved path of the executable if it exists."""
        if not self.provider:
            raise ProviderError("TerminalProvider has not been assigned to this tool.")

        path = self.provider.locate_executable(command)
        return {
            "command": command,
            "path": path,
            "found": path is not None,
            "status": "success",
        }