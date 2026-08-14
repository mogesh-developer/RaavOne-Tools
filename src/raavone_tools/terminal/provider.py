"""Terminal provider managing subprocess execution with safety boundaries."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import ProviderError, SecurityValidationError

logger = logging.getLogger(__name__)


class TerminalProvider(BaseProvider):
    """Resource provider that executes terminal commands constrained within a workspace root."""

    def __init__(self, workspace_root: Union[str, Path]) -> None:
        """Initialize the provider with a target workspace root."""
        self.workspace_root = Path(workspace_root).resolve()

    async def initialize(self) -> None:
        """Ensure the workspace root directory exists."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """No teardown needed for pure terminal provider."""
        pass

    def validate_working_dir(self, working_dir: Optional[Union[str, Path]] = None) -> Path:
        """Resolve the working directory and verify it is strictly within the workspace_root."""
        if working_dir is None:
            return self.workspace_root

        path_obj = Path(working_dir)

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
                f"Security Validation Error: Working directory '{working_dir}' lies outside "
                f"workspace boundary '{self.workspace_root}'."
            ) from e

        return resolved

    async def run_command(
        self,
        command: str,
        working_dir: Optional[Union[str, Path]] = None,
        timeout: int = 60,
        shell: bool = True,
    ) -> Dict[str, Any]:
        """Execute a shell command and return its exit code, stdout, and stderr."""
        cwd = self.validate_working_dir(working_dir)
        cwd.mkdir(parents=True, exist_ok=True)

        try:
            if shell:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    cwd=str(cwd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    *command.split(),
                    cwd=str(cwd),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

            logger.info("Running command '%s' in %s", command, cwd)
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise ProviderError(
                f"Command '{command}' timed out after {timeout} seconds."
            ) from None
        except Exception as e:
            raise ProviderError(f"Failed to run command '{command}': {e}") from e

        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }
