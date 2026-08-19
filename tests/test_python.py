import os
import tempfile
import pytest
from pathlib import Path

from raavone_tools.manager import ToolManager
from raavone_tools.python.provider import PythonProvider
from raavone_tools.python.tool import PythonExecuteTool, PythonRunFileTool, PythonEnvInfoTool
from raavone_tools.exceptions import SecurityValidationError, ExecutionError


@pytest.mark.asyncio
async def test_python_execute_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        manager = ToolManager()
        provider = PythonProvider(workspace_root=workspace_root)
        
        manager.register_tool(PythonExecuteTool(provider=provider))
        manager.register_tool(PythonRunFileTool(provider=provider))
        manager.register_tool(PythonEnvInfoTool(provider=provider))
        await manager.initialize_providers()
        
        try:
            # 1. Test standard execution (python_execute)
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

            # 4. Test Python Run File Tool
            script_path = workspace_root / "args_test.py"
            script_path.write_text("import sys\nprint(f'Received: {sys.argv[1]} and {sys.argv[2]}')")
            
            res_run_file = await manager.execute("python_run_file", {
                "script_path": "args_test.py",
                "args": ["val1", "val2"]
            })
            assert res_run_file["status"] == "success"
            assert res_run_file["stdout"] == "Received: val1 and val2"

            # 5. Test Python Env Info Tool
            res_env = await manager.execute("python_env_info", {})
            assert res_env["status"] == "success"
            assert "python_version" in res_env
            assert "executable_path" in res_env
            assert "pydantic" in res_env["installed_packages"]

        finally:
            await manager.close_providers()
