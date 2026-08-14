"""Filesystem provider enforcing safety boundaries."""

import os
from pathlib import Path
from typing import Union

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import SecurityValidationError


class FilesystemProvider(BaseProvider):
    """Resource provider that manages filesystem access, constraining operations within a workspace root."""

    def __init__(self, workspace_root: Union[str, Path]) -> None:
        """Initialize the provider with a target workspace root."""
        self.workspace_root = Path(workspace_root).resolve()

    async def initialize(self) -> None:
        """Ensure workspace directory exists."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """No teardown needed for pure filesystem provider."""
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
