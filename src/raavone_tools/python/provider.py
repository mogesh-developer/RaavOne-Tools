"""Python execution provider enforcing safety boundaries and asynchronous subprocess execution."""

import sys
import asyncio
from pathlib import Path
from typing import List, Tuple, Union

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import SecurityValidationError


class PythonProvider(BaseProvider):
    """Resource provider that manages secure python script execution inside a workspace root."""

    def __init__(self, workspace_root: Union[str, Path]) -> None:
        """Initialize the provider with a target workspace root."""
        self.workspace_root = Path(workspace_root).resolve()

    async def initialize(self) -> None:
        """Ensure workspace directory exists."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """No teardown needed for python provider."""
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

    async def run_python_script(self, script_path: Path, args: List[str] = None, timeout: int = 15) -> Tuple[int, str, str]:
        """Execute a python script file asynchronously using sys.executable with a timeout."""
        script_args = args if args else []
        cmd = [sys.executable, str(script_path)] + script_args
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace_root)
        )
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
            return process.returncode, stdout, stderr
        except asyncio.TimeoutError:
            try:
                process.terminate()
                await process.wait()
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
            raise TimeoutError(f"Python script execution timed out after {timeout} seconds.")
