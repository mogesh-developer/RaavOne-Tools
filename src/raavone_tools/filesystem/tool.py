"""Filesystem manipulation tools."""

import os
from typing import Any, Dict, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.filesystem.provider import FilesystemProvider


# --- Read File Tool ---

class ReadFileInput(BaseModel):
    """Input parameters for the read file tool."""
    path: str = Field(..., description="File path relative to workspace root")
    encoding: str = Field("utf-8", description="Character encoding to read the file")


class ReadFileTool(BaseTool[FilesystemProvider]):
    """Tool that reads file contents as text."""

    name: str = "read_file"
    description: str = "Read the contents of a file within the workspace."
    input_schema: Type[BaseModel] = ReadFileInput

    async def execute(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read and return content of verified path."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_path = self.provider.validate_path(path)
        try:
            if not safe_path.is_file():
                raise FileNotFoundError(f"File not found: '{path}'")
            
            content = safe_path.read_text(encoding=encoding)
            return {
                "path": path,
                "content": content,
                "status": "success",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to read file '{path}': {e}") from e


# --- Write File Tool ---

class WriteFileInput(BaseModel):
    """Input parameters for the write file tool."""
    path: str = Field(..., description="File path relative to workspace root")
    content: str = Field(..., description="Text content to write to the file")
    encoding: str = Field("utf-8", description="Character encoding to write the file")
    overwrite: bool = Field(True, description="Overwrite the file if it already exists")


class WriteFileTool(BaseTool[FilesystemProvider]):
    """Tool that writes content to a file, making parent directories if needed."""

    name: str = "write_file"
    description: str = "Write text content to a file within the workspace boundary."
    input_schema: Type[BaseModel] = WriteFileInput

    async def execute(
        self, path: str, content: str, encoding: str = "utf-8", overwrite: bool = True
    ) -> Dict[str, Any]:
        """Write content to verified path, enforcing overwrite protection if disabled."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_path = self.provider.validate_path(path)
        try:
            if safe_path.exists() and not overwrite:
                raise FileExistsError(f"File already exists: '{path}'")

            # Create parent directories dynamically
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding=encoding)
            
            return {
                "path": path,
                "bytes_written": len(content.encode(encoding)),
                "status": "success",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to write to file '{path}': {e}") from e


# --- List Directory Tool ---

class ListDirInput(BaseModel):
    """Input parameters for listing directories."""
    path: str = Field(".", description="Directory path relative to workspace root")


class ListDirTool(BaseTool[FilesystemProvider]):
    """Tool that lists directory entries."""

    name: str = "list_dir"
    description: str = "List all files and directories in a workspace directory."
    input_schema: Type[BaseModel] = ListDirInput

    async def execute(self, path: str = ".") -> Dict[str, Any]:
        """List and summarize directory entries under verified path."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_path = self.provider.validate_path(path)
        try:
            if not safe_path.is_dir():
                raise NotADirectoryError(f"Directory not found or invalid: '{path}'")

            items = []
            for entry in os.scandir(safe_path):
                # Compute path relative to workspace root
                rel_path = os.path.relpath(entry.path, self.provider.workspace_root)
                rel_path_str = rel_path.replace(os.path.sep, "/")
                
                info = {
                    "name": entry.name,
                    "path": rel_path_str,
                    "type": "directory" if entry.is_dir() else "file",
                }
                
                if entry.is_file():
                    try:
                        info["size"] = entry.stat().st_size
                    except Exception:
                        info["size"] = 0
                items.append(info)

            return {
                "path": path,
                "items": items,
                "status": "success",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to list directory '{path}': {e}") from e
