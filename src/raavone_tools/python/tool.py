"""Python execution tools."""

import uuid
from pathlib import Path
from typing import Any, Dict, Type
from pydantic import BaseModel, Field

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
