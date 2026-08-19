"""Python execution tools."""

import sys
import uuid
import platform
from pathlib import Path
from typing import Any, Dict, List, Type
from pydantic import BaseModel, Field

try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.python.provider import PythonProvider


# --- Python Execute Tool ---

class PythonExecuteInput(BaseModel):
    """Input parameters for Python script execution."""
    code: str = Field(..., description="Python source code to execute")
    timeout: int = Field(15, description="Maximum execution time in seconds (default: 15)")


class PythonExecuteTool(BaseTool[PythonProvider]):
    """Tool that executes inline Python code securely inside the workspace by running a temporary script."""

    name: str = "python_execute"
    description: str = "Run Python code asynchronously in a sandboxed subprocess and return stdout, stderr, and exit code."
    input_schema: Type[BaseModel] = PythonExecuteInput

    async def execute(self, code: str, timeout: int = 15) -> Dict[str, Any]:
        """Write the code to a temp script, execute, and return output details."""
        if not self.provider:
            raise ProviderError("PythonProvider has not been assigned to this tool.")

        # Create a unique temporary filename inside the workspace root
        temp_filename = f"_run_{uuid.uuid4().hex}.py"
        temp_filepath = self.provider.workspace_root / temp_filename

        try:
            # Write python script content
            temp_filepath.write_text(code, encoding="utf-8")

            # Validate path safety boundary
            self.provider.validate_path(temp_filepath)

            # Run script using the provider
            exit_code, stdout, stderr = await self.provider.run_python_script(temp_filepath, timeout=timeout)

            return {
                "status": "success" if exit_code == 0 else "failure",
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }

        except TimeoutError as te:
            return {
                "status": "timeout",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(te)
            }
        except Exception as e:
            raise ExecutionError(f"Failed to execute Python script: {e}") from e
        finally:
            # Guarantee cleanup of the temporary file
            if temp_filepath.exists():
                try:
                    temp_filepath.unlink()
                except Exception:
                    pass


# --- Python Run File Tool ---

class PythonRunFileInput(BaseModel):
    """Input parameters for running a Python script file."""
    script_path: str = Field(..., description="Path to the Python script relative to the workspace root")
    args: List[str] = Field(default=[], description="Command line arguments to pass to the script")
    timeout: int = Field(15, description="Maximum execution time in seconds (default: 15)")


class PythonRunFileTool(BaseTool[PythonProvider]):
    """Tool that executes an existing Python file inside the workspace root."""

    name: str = "python_run_file"
    description: str = "Run an existing Python file in the workspace with arguments and a timeout."
    input_schema: Type[BaseModel] = PythonRunFileInput

    async def execute(self, script_path: str, args: List[str] = [], timeout: int = 15) -> Dict[str, Any]:
        """Verify boundaries, and execute script."""
        if not self.provider:
            raise ProviderError("PythonProvider has not been assigned to this tool.")

        # Ensure script is inside workspace boundary
        real_script = self.provider.validate_path(script_path)

        if not real_script.exists() or not real_script.is_file():
            raise ExecutionError(f"Script file '{script_path}' does not exist or is not a file.")

        try:
            exit_code, stdout, stderr = await self.provider.run_python_script(real_script, args=args, timeout=timeout)
            return {
                "status": "success" if exit_code == 0 else "failure",
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }
        except TimeoutError as te:
            return {
                "status": "timeout",
                "exit_code": -1,
                "stdout": "",
                "stderr": str(te)
            }
        except Exception as e:
            raise ExecutionError(f"Failed to run script '{script_path}': {e}") from e


# --- Python Environment Info Tool ---

class PythonEnvInfoInput(BaseModel):
    """Input parameters for getting environment info."""
    pass


class PythonEnvInfoTool(BaseTool[PythonProvider]):
    """Tool that retrieves python interpreter version and lists installed packages."""

    name: str = "python_env_info"
    description: str = "Get active Python version, system platform, executable path, and lists of installed pip libraries."
    input_schema: Type[BaseModel] = PythonEnvInfoInput

    async def execute(self) -> Dict[str, Any]:
        """Fetch details of python executable and libs."""
        packages = {}
        try:
            for dist in importlib_metadata.distributions():
                name = dist.metadata.get("Name")
                if name:
                    packages[name.lower()] = dist.version
        except Exception:
            pass

        return {
            "status": "success",
            "python_version": sys.version,
            "executable_path": sys.executable,
            "platform": platform.platform(),
            "installed_packages": packages
        }
