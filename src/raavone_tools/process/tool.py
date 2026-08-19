"""Process execution tools.

This module provides a set of tools for managing system processes. It relies on
`psutil` for detailed process information and `subprocess` for starting and
stopping background commands. All spawned processes are tracked in the
`ProcessProvider.active_processes` registry so they can be inspected, stopped,
or waited on later.
"""

import os
import subprocess
import psutil
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.process.provider import ProcessProvider

# --- Process List Tool ---

class ProcessListInput(BaseModel):
    """Input parameters for listing processes."""
    name_filter: Optional[str] = Field(None, description="Case-insensitive filter matching process name (e.g. 'python')")
    limit: int = Field(50, description="Max number of process items to return (default: 50)")


class ProcessListTool(BaseTool[ProcessProvider]):
    """Tool that lists currently running system processes."""

    name: str = "process_list"
    description: str = "List running processes with PID, name, status, CPU, and memory stats."
    input_schema: Type[BaseModel] = ProcessListInput

    async def execute(self, name_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        processes = []
        filter_lower = name_filter.lower() if name_filter else None

        for proc in psutil.process_iter(["pid", "name", "status"]):
            try:
                proc_info = proc.info
                name = proc_info.get("name") or ""
                if filter_lower and filter_lower not in name.lower():
                    continue
                try:
                    cpu = proc.cpu_percent(interval=None)
                    mem = proc.memory_percent()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cpu = 0.0
                    mem = 0.0
                processes.append({
                    "pid": proc_info["pid"],
                    "name": name,
                    "status": proc_info["status"],
                    "cpu_percent": round(cpu, 2),
                    "memory_percent": round(mem, 2),
                })
                if len(processes) >= limit:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {"status": "success", "processes": processes, "count": len(processes)}

# --- Process Start Tool ---

class ProcessStartInput(BaseModel):
    """Input parameters for starting a process."""
    command: str = Field(..., description="Shell command to start the background process (e.g. 'python app.py')")
    working_dir: Optional[str] = Field(None, description="Optional working directory path relative to workspace root")


class ProcessStartTool(BaseTool[ProcessProvider]):
    """Tool that starts a long‑running program in the background."""

    name: str = "process_start"
    description: str = "Start a background program/process and return its PID."
    input_schema: Type[BaseModel] = ProcessStartInput

    async def execute(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("ProcessProvider has not been assigned to this tool.")

        cwd_path = None
        if working_dir:
            cwd_path = str(os.path.abspath(working_dir))

        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.provider.register_process(proc.pid, proc)
            return {"status": "success", "pid": proc.pid, "command": command}
        except Exception as e:
            raise ExecutionError(f"Failed to start process: {e}") from e

# --- Process Stop Tool ---

class ProcessStopInput(BaseModel):
    """Input parameters for stopping a process."""
    pid: int = Field(..., description="Process ID (PID) of the program to stop")


class ProcessStopTool(BaseTool[ProcessProvider]):
    """Tool that terminates a process by PID."""

    name: str = "process_stop"
    description: str = "Stop/kill a running process by its PID."
    input_schema: Type[BaseModel] = ProcessStopInput

    async def execute(self, pid: int) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("ProcessProvider has not been assigned to this tool.")
        # Remove from registry if present
        self.provider.unregister_process(pid)
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
            return {"status": "success", "pid": pid, "message": f"Terminated PID {pid}."}
        except psutil.NoSuchProcess:
            return {"status": "success", "pid": pid, "message": "Process does not exist."}
        except psutil.AccessDenied:
            raise ExecutionError(f"Access denied: cannot terminate PID {pid}.")
        except Exception as e:
            raise ExecutionError(f"Failed to stop process: {e}") from e

# --- Process Info Tool ---

class ProcessInfoInput(BaseModel):
    """Input parameters for querying process information."""
    pid: int = Field(..., description="Process ID (PID) to query")


class ProcessInfoTool(BaseTool[ProcessProvider]):
    """Tool that retrieves detailed system metrics for a specific process PID."""

    name: str = "process_info"
    description: str = "Get detailed configuration, CPU, memory, and port mappings of a process by PID."
    input_schema: Type[BaseModel] = ProcessInfoInput

    async def execute(self, pid: int) -> Dict[str, Any]:
        try:
            proc = psutil.Process(pid)
            # Connections
            connections = []
            try:
                conn_fn = getattr(proc, "net_connections", getattr(proc, "connections", None))
                if conn_fn:
                    for conn in conn_fn():
                        connections.append({
                            "fd": conn.fd,
                            "type": str(conn.type),
                            "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            "status": conn.status,
                        })
            except (psutil.AccessDenied, AttributeError):
                pass
            # Memory
            try:
                mem = proc.memory_info()
                rss, vms = mem.rss, mem.vms
            except psutil.AccessDenied:
                rss = vms = 0
            return {
                "status": "success",
                "pid": pid,
                "name": proc.name(),
                "status_state": proc.status(),
                "cmdline": proc.cmdline(),
                "cpu_percent": round(proc.cpu_percent(interval=None), 2),
                "rss_bytes": rss,
                "vms_bytes": vms,
                "connections": connections,
            }
        except psutil.NoSuchProcess:
            raise ExecutionError(f"Process with PID {pid} does not exist.")
        except psutil.AccessDenied:
            raise ExecutionError(f"Access denied: cannot read PID {pid}.")
        except Exception as e:
            raise ExecutionError(f"Failed to get process info: {e}") from e

# --- Process Restart Tool ---

class ProcessRestartInput(BaseModel):
    """Input for restarting an existing process by PID."""
    pid: int = Field(..., description="PID of the process to restart")


class ProcessRestartTool(BaseTool[ProcessProvider]):
    """Tool that restarts a process using its original command line.

    The tool fetches the command line of the target process, stops it, and then
    spawns a new process with the same command. The new PID is returned.
    """

    name: str = "process_restart"
    description: str = "Restart a running process by PID using its original command line."
    input_schema: Type[BaseModel] = ProcessRestartInput

    async def execute(self, pid: int) -> Dict[str, Any]:
        if not self.provider:
            raise ProviderError("ProcessProvider not assigned.")
        try:
            proc = psutil.Process(pid)
            cmdline = proc.cmdline()
            cwd = proc.cwd()
        except psutil.NoSuchProcess:
            raise ExecutionError(f"Process with PID {pid} does not exist.")
        except Exception as e:
            raise ExecutionError(f"Unable to retrieve command for PID {pid}: {e}")

        # Stop the old process
        stop_tool = ProcessStopTool(self.provider)
        await stop_tool.execute(pid=pid)

        # Start a new process with the same command line
        command = " ".join(cmdline) if isinstance(cmdline, list) else cmdline
        start_tool = ProcessStartTool(self.provider)
        result = await start_tool.execute(command=command, working_dir=cwd)
        return {"status": "success", "old_pid": pid, "new_pid": result.get("pid"), "message": "Process restarted."}

# --- Process Resources Tool ---

class ProcessResourcesInput(BaseModel):
    """Input for fetching resource usage of a process."""
    pid: int = Field(..., description="PID of the process to inspect")


class ProcessResourcesTool(BaseTool[ProcessProvider]):
    """Tool that returns CPU and memory usage for a given PID."""

    name: str = "process_resources"
    description: str = "Get CPU percent and memory usage of a process."
    input_schema: Type[BaseModel] = ProcessResourcesInput

    async def execute(self, pid: int) -> Dict[str, Any]:
        try:
            proc = psutil.Process(pid)
            cpu = proc.cpu_percent(interval=0.1)
            mem = proc.memory_percent()
            return {"status": "success", "pid": pid, "cpu_percent": round(cpu, 2), "memory_percent": round(mem, 2)}
        except psutil.NoSuchProcess:
            raise ExecutionError(f"PID {pid} does not exist.")
        except Exception as e:
            raise ExecutionError(f"Failed to fetch resources: {e}")

# --- Process Output Tool ---

class ProcessOutputInput(BaseModel):
    """Input for capturing stdout/stderr of a tracked process."""
    pid: int = Field(..., description="PID of the process whose output should be captured")
    timeout: int = Field(5, description="Maximum seconds to wait for output (default 5)")


class ProcessOutputTool(BaseTool[ProcessProvider]):
    """Tool that reads the stdout/stderr of a background process.

    It only works for processes that were started via `ProcessStartTool` which
    records the `subprocess.Popen` object with pipes enabled.
    """

    name: str = "process_output"
    description: str = "Capture stdout and stderr of a managed background process."
    input_schema: Type[BaseModel] = ProcessOutputInput

    async def execute(self, pid: int, timeout: int = 5) -> Dict[str, Any]:
        proc = self.provider.active_processes.get(pid)
        if not proc:
            raise ExecutionError(f"No tracked process with PID {pid}.")
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            return {"status": "success", "pid": pid, "stdout": stdout, "stderr": stderr}
        except subprocess.TimeoutExpired:
            raise ExecutionError(f"Process {pid} did not produce output within {timeout}s.")
        except Exception as e:
            raise ExecutionError(f"Failed to capture output: {e}")

# --- Process Wait Tool ---

class ProcessWaitInput(BaseModel):
    """Input for waiting on a process to finish."""
    pid: int = Field(..., description="PID of the process to wait for")
    timeout: Optional[int] = Field(None, description="Maximum seconds to wait (None = indefinite)")


class ProcessWaitTool(BaseTool[ProcessProvider]):
    """Tool that blocks until the specified process exits or timeout elapses."""

    name: str = "process_wait"
    description: str = "Wait for a process to terminate, optionally with a timeout."
    input_schema: Type[BaseModel] = ProcessWaitInput

    async def execute(self, pid: int, timeout: Optional[int] = None) -> Dict[str, Any]:
        proc = self.provider.active_processes.get(pid)
        if not proc:
            raise ExecutionError(f"No tracked process with PID {pid}.")
        try:
            proc.wait(timeout=timeout)
            return {"status": "success", "pid": pid, "message": "Process terminated."}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "pid": pid, "message": f"Process still running after {timeout}s."}
        except Exception as e:
            raise ExecutionError(f"Error waiting for process: {e}")
