"""Process provider managing background processes and system resources."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import subprocess

from raavone_tools.base import BaseProvider


class ProcessProvider(BaseProvider):
    """Resource provider that manages background process lifecycles and queries active processes."""

    def __init__(self) -> None:
        """Initialize the process provider with an empty process registry."""
        self.active_processes: Dict[int, subprocess.Popen] = {}

    async def initialize(self) -> None:
        """Startup process provider."""
        pass

    async def close(self) -> None:
        """Terminate all background processes started by the agent on cleanup."""
        for pid, process in list(self.active_processes.items()):
            try:
                process.terminate()
                process.wait(timeout=2)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        self.active_processes.clear()

    def register_process(self, pid: int, process: subprocess.Popen) -> None:
        """Register a new subprocess."""
        self.active_processes[pid] = process

    def unregister_process(self, pid: int) -> None:
        """Remove a process from the registry."""
        if pid in self.active_processes:
            del self.active_processes[pid]
