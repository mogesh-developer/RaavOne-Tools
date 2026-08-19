"""Terminal provider managing subprocess execution with safety boundaries."""

import asyncio
import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import ProviderError, SecurityValidationError

logger = logging.getLogger(__name__)

# Environment variable names (case-insensitive) considered secret and
# stripped from the base environment passed to subprocesses.
_SENSITIVE_ENV_PATTERNS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "secret_key",
    "auth",
    "credential",
    "cred",
    "private_key",
    "session",
    "signature",
)

# Regex patterns for destructive / system-level commands blocked by default.
_DANGEROUS_PATTERNS: List[re.Pattern] = [
    re.compile(r"\brm\s+.*-r[a-z0-9]*f?[a-z0-9]*\s+/\*?(?:\s|$)", re.IGNORECASE),
    re.compile(r"\brm\s+.*-r[a-z0-9]*f?[a-z0-9]*\s+~(?:\s|$)", re.IGNORECASE),
    re.compile(r"\b(rmdir|rd)\s+[/~]", re.IGNORECASE),
    re.compile(r"\b(del|erase)\s+.*[/~]", re.IGNORECASE),
    re.compile(r"\b(mkfs|fdisk|gparted|format)\b", re.IGNORECASE),
    re.compile(r"\bdd\s+.*\bif=.*\bof=.*", re.IGNORECASE),
    re.compile(r"\b(shutdown|reboot|halt|poweroff)\b", re.IGNORECASE),
    re.compile(r"\b:\(\)\s*\{\s*:\|:&", re.IGNORECASE),
    re.compile(r"\bchmod\s+.*(?:777|666)\s+[/~]", re.IGNORECASE),
    re.compile(r"\bsudo\s+rm\b", re.IGNORECASE),
]

_TIMEOUT_KILL_WAIT = 5.0


def _is_sensitive_env_name(name: str) -> bool:
    """Return True if the environment variable name looks like a secret."""
    lowered = name.lower()
    return any(pattern in lowered for pattern in _SENSITIVE_ENV_PATTERNS)


def _check_dangerous_command(command: str) -> None:
    """Raise SecurityValidationError if the command matches a dangerous pattern."""
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(command):
            raise SecurityValidationError(
                f"Security Validation Error: Command '{command}' matches the "
                f"blocked pattern '{pattern.pattern}'. Set allow_dangerous=True to override."
            )


def _truncate_output(text: str, max_chars: Optional[int]) -> tuple:
    """Truncate the text to max_chars, returning (text, truncated_flag)."""
    if max_chars is None or len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


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

    def build_env(
        self,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Build a bounded environment for subprocesses.

        The base environment is filtered to drop sensitive variables (API keys,
        tokens, passwords, etc.), then user-supplied variables are merged on top.
        """
        base_env = {
            name: value
            for name, value in os.environ.items()
            if not _is_sensitive_env_name(name)
        }
        if env:
            base_env.update(env)
        return base_env

    def redact(self, text: str, secrets: List[str]) -> str:
        """Replace occurrences of secret values with a placeholder."""
        if not secrets:
            return text
        redacted = text
        for secret in secrets:
            if secret:
                redacted = redacted.replace(secret, "***")
        return redacted

    async def run_command(
        self,
        command: str,
        working_dir: Optional[Union[str, Path]] = None,
        timeout: int = 60,
        shell: bool = True,
        env: Optional[Dict[str, str]] = None,
        stdin: Optional[str] = None,
        max_output_chars: Optional[int] = None,
        allow_dangerous: bool = False,
    ) -> Dict[str, Any]:
        """Execute a shell command and return its exit code, stdout, and stderr."""
        if not allow_dangerous:
            _check_dangerous_command(command)

        cwd = self.validate_working_dir(working_dir)
        cwd.mkdir(parents=True, exist_ok=True)
        child_env = self.build_env(env)

        # Collect secret values to redact from command output/logs.
        secret_values = [value for name, value in child_env.items() if _is_sensitive_env_name(name)]

        stdin_bytes = stdin.encode("utf-8") if stdin is not None else None

        kwargs: Dict[str, Any] = {
            "cwd": str(cwd),
            "env": child_env,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "stdin": asyncio.subprocess.PIPE if stdin_bytes is not None else None,
        }
        if os.name == "nt":
            kwargs["creationflags"] = 0x00000200  # CREATE_NEW_PROCESS_GROUP

        start = time.monotonic()
        proc: Optional[Any] = None
        try:
            if shell:
                proc = await asyncio.create_subprocess_shell(command, **kwargs)
            else:
                proc = await asyncio.create_subprocess_exec(*command.split(), **kwargs)

            logger.info("Running command '%s' in %s", command, cwd)
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes), timeout=timeout
            )
        except asyncio.TimeoutError:
            await self._kill_process_tree(proc)
            raise ProviderError(
                f"Command '{command}' timed out after {timeout} seconds."
            ) from None
        except Exception as e:
            await self._kill_process_tree(proc)
            raise ProviderError(f"Failed to run command '{command}': {e}") from e

        duration = round(time.monotonic() - start, 2)

        raw_stdout = stdout.decode(errors="replace") if stdout else ""
        raw_stderr = stderr.decode(errors="replace") if stderr else ""

        if secret_values:
            raw_stdout = self.redact(raw_stdout, secret_values)
            raw_stderr = self.redact(raw_stderr, secret_values)

        stdout_limited, stdout_truncated = _truncate_output(raw_stdout, max_output_chars)
        stderr_limited, stderr_truncated = _truncate_output(raw_stderr, max_output_chars)

        return {
            "exit_code": proc.returncode,
            "stdout": stdout_limited,
            "stderr": stderr_limited,
            "duration": duration,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated if stderr else False,
        }

    @staticmethod
    async def _kill_process_tree(proc: Optional[Any]) -> None:
        """Best-effort kill of a process and its children (with timeout)."""
        if proc is None:
            return

        if os.name == "nt":
            # Kill the whole process tree first so orphaned children die too.
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                )
            except Exception:
                pass

        try:
            proc.kill()
        except Exception:
            pass
        try:
            await asyncio.wait_for(proc.wait(), timeout=_TIMEOUT_KILL_WAIT)
        except (asyncio.TimeoutError, ProcessLookupError):
            pass

    def locate_executable(self, command: str) -> Optional[str]:
        """Locate an executable using the platform-appropriate resolver."""
        return shutil.which(command)