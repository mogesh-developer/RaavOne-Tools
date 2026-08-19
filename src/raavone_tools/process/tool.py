"""Process execution tools."""

import os
import subprocess
from typing import Any, Dict, List, Optional, Type
import psutil
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
        """Iterate running processes and return details."""
        processes = []
        filter_lower = name_filter.lower() if name_filter else None

        for proc in psutil.process_iter(["pid", "name", "status"]):
            try:
                proc_info = proc.info
                name = proc_info.get("name") or ""
                
                # Apply name filter
                if filter_lower and filter_lower not in name.lower():
                    continue

                # Fetch basic cpu/mem info safely
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

        return {
            "status": "success",
            "processes": processes,
            "count": len(processes)
        }


# --- Process Start Tool ---

class ProcessStartInput(BaseModel):
    """Input parameters for starting a process."""
    command: str = Field(..., description="Shell command to start the background process (e.g. 'python app.py')")
    working_dir: Optional[str] = Field(None, description="Optional working directory path relative to workspace root")


class ProcessStartTool(BaseTool[ProcessProvider]):
    """Tool that starts a long-running program in the background."""

    name: str = "process_start"
    description: str = "Start a background program/process and return its PID."
    input_schema: Type[BaseModel] = ProcessStartInput

    async def execute(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Spawn the process in background."""
        if not self.provider:
            raise ProviderError("ProcessProvider has not been assigned to this tool.")

        cwd_path = None
        if working_dir:
            # Let terminal provider handle boundaries, or direct resolve.
            # We can use default Path resolution relative to current folder or root.
            cwd_path = str(Path(working_dir).resolve())

        try:
            # Spawn process without blocking (stdout/stderr directed to DEVNULL to avoid buffer blocking)
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Register it
            self.provider.register_process(proc.pid, proc)

            return {
                "status": "success",
                "pid": proc.pid,
                "command": command,
                "message": f"Successfully spawned background process with PID {proc.pid}."
            }
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
        """Find the process and stop it."""
        if not self.provider:
            raise ProviderError("ProcessProvider has not been assigned to this tool.")

        try:
            # Unregister it from tracking if it was registered
            self.provider.unregister_process(pid)

            proc = psutil.Process(pid)
            proc.terminate()
            
            # Wait up to 3 seconds for clean exit
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                # Force kill
                proc.kill()

            return {
                "status": "success",
                "pid": pid,
                "message": f"Successfully terminated process with PID {pid}."
            }
        except psutil.NoSuchProcess:
            return {
                "status": "success",
                "pid": pid,
                "message": f"Process with PID {pid} is already stopped or does not exist."
            }
        except psutil.AccessDenied:
            raise ExecutionError(f"Access denied: Cannot terminate process with PID {pid}.")
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
        """Fetch details using psutil."""
        try:
            proc = psutil.Process(pid)
            
            # Fetch connections (ports) safely
            connections = []
            try:
                connections_fn = getattr(proc, "net_connections", getattr(proc, "connections", None))
                if connections_fn:
                    for conn in connections_fn():
                        connections.append({
                            "fd": conn.fd,
                            "type": str(conn.type),
                            "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            "status": conn.status
                        })
            except (psutil.AccessDenied, AttributeError):
                pass

            # Fetch memory stats
            try:
                mem_info = proc.memory_info()
                rss = mem_info.rss
                vms = mem_info.vms
            except psutil.AccessDenied:
                rss = 0
                vms = 0

            return {
                "status": "success",
                "pid": pid,
                "name": proc.name(),
                "status_state": proc.status(),
                "cmdline": proc.cmdline(),
                "cpu_percent": round(proc.cpu_percent(interval=None), 2),
                "rss_bytes": rss,
                "vms_bytes": vms,
                "connections": connections
            }
        except psutil.NoSuchProcess:
            raise ExecutionError(f"Process with PID {pid} does not exist.")
        except psutil.AccessDenied:
            raise ExecutionError(f"Access denied: Cannot read process stats for PID {pid}.")
        except Exception as e:
            raise ExecutionError(f"Failed to get process info: {e}") from e
