"""Archive execution tools."""

import os
from pathlib import Path
from typing import Any, Dict, List, Type
import zipfile
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError, SecurityValidationError
from raavone_tools.archive.provider import ArchiveProvider


# --- Create Archive Tool ---

class CreateArchiveInput(BaseModel):
    """Input parameters for creating an archive."""
    source_path: str = Field(..., description="Path of the file or directory to compress")
    archive_path: str = Field(..., description="Destination filepath of the generated zip archive (must end with .zip)")


class CreateArchiveTool(BaseTool[ArchiveProvider]):
    """Tool that creates a ZIP archive from a file or folder within the workspace boundary."""

    name: str = "archive_create"
    description: str = "Create a ZIP archive from a file or folder."
    input_schema: Type[BaseModel] = CreateArchiveInput

    async def execute(self, source_path: str, archive_path: str) -> Dict[str, Any]:
        """Compress the source path into a ZIP archive."""
        if not self.provider:
            raise ProviderError("ArchiveProvider has not been assigned to this tool.")

        try:
            source_real = self.provider.validate_path(source_path)
            archive_real = self.provider.validate_path(archive_path)

            if not source_real.exists():
                raise ExecutionError(f"Source path '{source_path}' does not exist.")

            if not archive_real.name.endswith(".zip"):
                raise ExecutionError("Destination archive name must end with '.zip'")

            # Ensure parent folder for zip exists
            archive_real.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(archive_real, "w", zipfile.ZIP_DEFLATED) as zip_ref:
                if source_real.is_dir():
                    # Walk directory and add files
                    for root, _, files in os.walk(source_real):
                        for file in files:
                            file_path = Path(root) / file
                            # Calculate relative path inside the zip file
                            archive_name = file_path.relative_to(source_real)
                            zip_ref.write(file_path, archive_name)
                else:
                    # Write single file
                    zip_ref.write(source_real, source_real.name)

            return {
                "status": "success",
                "archive_path": str(archive_real.resolve()),
                "message": f"Successfully created archive at '{archive_path}' from '{source_path}'."
            }
        except SecurityValidationError:
            raise
        except Exception as e:
            raise ExecutionError(f"Failed to create archive: {e}") from e


# --- Extract Archive Tool ---

class ExtractArchiveInput(BaseModel):
    """Input parameters for extracting an archive."""
    archive_path: str = Field(..., description="Path of the ZIP archive file to extract")
    dest_path: str = Field(..., description="Destination directory path where files should be extracted")


class ExtractArchiveTool(BaseTool[ArchiveProvider]):
    """Tool that extracts a ZIP archive to a destination directory, with Zip Slip security prevention."""

    name: str = "archive_extract"
    description: str = "Extract the contents of a ZIP archive to a target directory."
    input_schema: Type[BaseModel] = ExtractArchiveInput

    async def execute(self, archive_path: str, dest_path: str) -> Dict[str, Any]:
        """Extract all members from the archive safely."""
        if not self.provider:
            raise ProviderError("ArchiveProvider has not been assigned to this tool.")

        try:
            archive_real = self.provider.validate_path(archive_path)
            dest_real = self.provider.validate_path(dest_path)

            if not archive_real.exists():
                raise ExecutionError(f"Archive file '{archive_path}' does not exist.")

            # Create destination folder
            dest_real.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(archive_real, "r") as zip_ref:
                # Zip Slip mitigation: Verify all paths resolve within the target directory
                for member in zip_ref.namelist():
                    # Construct target path and resolve
                    target_member_path = Path(dest_real) / member
                    try:
                        target_member_path.resolve().relative_to(dest_real.resolve())
                    except ValueError as e:
                        raise SecurityValidationError(
                            f"Security boundary breach: Malicious archive member '{member}' "
                            f"attempts to extract outside target '{dest_path}'."
                        ) from e

                # Safe to extract
                zip_ref.extractall(dest_real)

            return {
                "status": "success",
                "dest_path": str(dest_real.resolve()),
                "message": f"Successfully extracted archive '{archive_path}' to '{dest_path}'."
            }
        except SecurityValidationError:
            raise
        except Exception as e:
            raise ExecutionError(f"Failed to extract archive: {e}") from e


# --- List Archive Tool ---

class ListArchiveInput(BaseModel):
    """Input parameters for listing archive contents."""
    archive_path: str = Field(..., description="Path of the ZIP archive file to list")


class ListArchiveTool(BaseTool[ArchiveProvider]):
    """Tool that lists the members and details inside a ZIP archive."""

    name: str = "archive_list"
    description: str = "List all files and compression details inside a ZIP archive."
    input_schema: Type[BaseModel] = ListArchiveInput

    async def execute(self, archive_path: str) -> Dict[str, Any]:
        """Read zipfile central directory and return file details."""
        if not self.provider:
            raise ProviderError("ArchiveProvider has not been assigned to this tool.")

        try:
            archive_real = self.provider.validate_path(archive_path)

            if not archive_real.exists():
                raise ExecutionError(f"Archive file '{archive_path}' does not exist.")

            files = []
            with zipfile.ZipFile(archive_real, "r") as zip_ref:
                for info in zip_ref.infolist():
                    files.append({
                        "filename": info.filename,
                        "file_size": info.file_size,
                        "compress_size": info.compress_size,
                        "is_dir": info.is_dir()
                    })

            return {
                "status": "success",
                "files": files,
                "count": len(files)
            }
        except SecurityValidationError:
            raise
        except Exception as e:
            raise ExecutionError(f"Failed to list archive contents: {e}") from e
