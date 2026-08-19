import os
import time
import pytest

from raavone_tools.manager import ToolManager
from raavone_tools.process.provider import ProcessProvider
from raavone_tools.process.tool import (
    ProcessListTool,
    ProcessStartTool,
    ProcessStopTool,
    ProcessInfoTool,
)


@pytest.mark.asyncio
async def test_process_lifecycle():
    manager = ToolManager()
    provider = ProcessProvider()
    
    manager.register_tool(ProcessListTool(provider=provider))
    manager.register_tool(ProcessStartTool(provider=provider))
    manager.register_tool(ProcessStopTool(provider=provider))
    manager.register_tool(ProcessInfoTool(provider=provider))
    
    await manager.initialize_providers()
    
    try:
        # 1. Start a long running background python process
        cmd = 'python -c "import time; time.sleep(20)"'
        res_start = await manager.execute("process_start", {"command": cmd})
        assert res_start["status"] == "success"
        pid = res_start["pid"]
        assert pid > 0
        
        # Give process a moment to spawn
        time.sleep(0.5)

        # 2. Get process info
        res_info = await manager.execute("process_info", {"pid": pid})
        assert res_info["status"] == "success"
        assert res_info["pid"] == pid
        proc_name = res_info["name"].lower()
        assert any(x in proc_name for x in ("python", "cmd", "sh", "bash"))

        # 3. List processes with filter (use the spawned process name to filter)
        res_list = await manager.execute("process_list", {"name_filter": res_info["name"]})
        assert res_list["status"] == "success"
        pids = {p["pid"] for p in res_list["processes"]}
        assert pid in pids

        # 4. Stop process
        res_stop = await manager.execute("process_stop", {"pid": pid})
        assert res_stop["status"] == "success"
        
        # Wait a moment for termination
        time.sleep(0.5)

        # Verify stopped (should raise ExecutionError since it does not exist anymore)
        with pytest.raises(Exception):
            await manager.execute("process_info", {"pid": pid})

    finally:
        await manager.close_providers()
