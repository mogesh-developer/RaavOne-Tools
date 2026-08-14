"""Terminal execution tools."""

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.terminal.provider import TerminalProvider


# --- Run Command Tool ---

class RunCommandInput(BaseModel):
    """Input parameters for the run command tool."""
    command: str = Field(..., description="Shell command to execute")
    working_dir: Optional[str] = Field(
        None,
        description="Working directory path relative to workspace root",
    )
    timeout: int = Field(60, description="Maximum execution time in seconds")
    shell: bool = Field(True, description="Run the command through a shell")


class RunCommandTool(BaseTool[TerminalProvider]):
    """Tool that executes a terminal command within the workspace boundary."""

    name: str = "run_command"
    description: str = "Execute a shell command within the workspace and return its output."
    input_schema: Type[BaseModel] = RunCommandInput

    async def execute(
        self,
        command: str,
        working_dir: Optional[str] = None,
        timeout: int = 60,
        shell: bool = True,
    ) -> Dict[str, Any]:
        """Run the command and return its exit code, stdout, and stderr."""
        if not self.provider:
            raise ProviderError("TerminalProvider has not been assigned to this tool.")

        try:
            result = await self.provider.run_command(
                command,
                working_dir=working_dir,
                timeout=timeout,
                shell=shell,
            )
            return {
                "command": command,
                "exit_code": result["exit_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "status": "success",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to run command '{command}': {e}") from e
