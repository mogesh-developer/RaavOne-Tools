import os
import tempfile
import pytest
from pathlib import Path

from raavone_tools.manager import ToolManager
from raavone_tools.python.provider import PythonProvider
from raavone_tools.python.tool import PythonExecuteTool
from raavone_tools.exceptions import SecurityValidationError, ExecutionError


@pytest.mark.asyncio
async def test_python_execute_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        manager = ToolManager()
        provider = PythonProvider(workspace_root=workspace_root)
        
        manager.register_tool(PythonExecuteTool(provider=provider))
        await manager.initialize_providers()
        
        try:
            # 1. Test standard execution
            code_ok = "numbers = [10, 20, 30]\nprint(sum(numbers)/len(numbers))"
            res_ok = await manager.execute("python_execute", {"code": code_ok})
            assert res_ok["status"] == "success"
            assert res_ok["exit_code"] == 0
            assert res_ok["stdout"] == "20.0"
            assert res_ok["stderr"] == ""

            # 2. Test syntax error / exception execution
            code_fail = "import sys\nprint('starting')\nraise ValueError('Test Failure')"
            res_fail = await manager.execute("python_execute", {"code": code_fail})
            assert res_fail["status"] == "failure"
            assert res_fail["exit_code"] != 0
            assert res_fail["stdout"] == "starting"
            assert "ValueError: Test Failure" in res_fail["stderr"]

            # 3. Test timeout execution
            code_timeout = "import time\ntime.sleep(5)\nprint('done')"
            res_timeout = await manager.execute("python_execute", {"code": code_timeout, "timeout": 1})
            assert res_timeout["status"] == "timeout"
            assert res_timeout["exit_code"] == -1
            assert "timed out after 1 seconds" in res_timeout["stderr"]

        finally:
            await manager.close_providers()
