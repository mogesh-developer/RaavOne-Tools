"""Archive provider enforcing safety boundaries."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import SecurityValidationError


class ArchiveProvider(BaseProvider):
    """Resource provider that manages archive file access, constraining operations within a workspace root."""

    def __init__(self, workspace_root: Union[str, Path]) -> None:
        """Initialize the provider with a target workspace root."""
        self.workspace_root = Path(workspace_root).resolve()

    async def initialize(self) -> None:
        """Ensure workspace directory exists."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """No teardown needed for archive provider."""
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
    async def info(self, archive_path: Union[str, Path]) -> Dict[str, Any]:
        """Return basic info about a ZIP archive (type, entry count, total size)."""
        archive_real = self.validate_path(archive_path)
        if not archive_real.exists():
            raise ExecutionError(f"Archive file '{archive_path}' does not exist.")
        if not archive_real.name.endswith('.zip'):
            raise ExecutionError("Only .zip archives are supported for info.")
        with zipfile.ZipFile(archive_real, 'r') as zf:
            info = {
                "type": "zip",
                "entry_count": len(zf.infolist()),
                "total_uncompressed_size": sum(i.file_size for i in zf.infolist()),
                "total_compressed_size": sum(i.compress_size for i in zf.infolist()),
            }
        return info

    async def create_tar(self, source_path: Union[str, Path], archive_path: Union[str, Path], compression: str = "gz") -> Dict[str, Any]:
        """Create a TAR (optionally compressed) archive from source_path."""
        source_real = self.validate_path(source_path)
        archive_real = self.validate_path(archive_path)
        mode = f"w:{compression}" if compression in ("gz", "bz2") else "w"
        archive_real.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_real, mode) as tar:
            tar.add(source_real, arcname=source_real.name)
        return {"status": "success", "archive_path": str(archive_real.resolve())}

    async def extract_tar(self, archive_path: Union[str, Path], dest_path: Union[str, Path], members: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract a TAR archive safely, optionally extracting only specified members."""
        archive_real = self.validate_path(archive_path)
        dest_real = self.validate_path(dest_path)
        dest_real.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_real, 'r') as tar:
            if members:
                safe_members = []
                for member in members:
                    ti = tar.getmember(member)
                    target_path = dest_real / ti.name
                    target_path.resolve().relative_to(dest_real.resolve())
                    safe_members.append(ti)
                tar.extractall(dest_real, members=safe_members)
            else:
                # Safety check for all members
                for member in tar.getmembers():
                    target_path = dest_real / member.name
                    target_path.resolve().relative_to(dest_real.resolve())
                tar.extractall(dest_real)
        return {"status": "success", "dest_path": str(dest_real.resolve())}

    async def selective_extract(self, archive_path: Union[str, Path], dest_path: Union[str, Path], include_patterns: List[str]) -> Dict[str, Any]:
        """Extract only files matching include_patterns (glob) from a ZIP archive."""
        import fnmatch
        archive_real = self.validate_path(archive_path)
        dest_real = self.validate_path(dest_path)
        dest_real.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_real, 'r') as zip_ref:
            for info in zip_ref.infolist():
                if any(fnmatch.fnmatch(info.filename, pat) for pat in include_patterns):
                    target_path = dest_real / info.filename
                    target_path.resolve().relative_to(dest_real.resolve())
                    zip_ref.extract(info, dest_real)
        return {"status": "success", "dest_path": str(dest_real.resolve())}
