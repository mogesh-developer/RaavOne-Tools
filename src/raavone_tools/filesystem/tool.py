"""Filesystem manipulation tools."""

import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Type
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


# --- Delete File Tool ---

class DeleteFileInput(BaseModel):
    """Input parameters for the delete file tool."""
    path: str = Field(..., description="File path relative to workspace root")


class DeleteFileTool(BaseTool[FilesystemProvider]):
    """Tool that deletes a file within the workspace."""

    name: str = "delete_file"
    description: str = "Delete a file inside the workspace boundary."
    input_schema: Type[BaseModel] = DeleteFileInput

    async def execute(self, path: str) -> Dict[str, Any]:
        """Delete the file at verified path."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_path = self.provider.validate_path(path)
        try:
            if not safe_path.is_file():
                raise FileNotFoundError(f"File not found or not a file: '{path}'")
            safe_path.unlink()
            return {"path": path, "status": "success"}
        except Exception as e:
            raise ExecutionError(f"Failed to delete file '{path}': {e}") from e


# --- Create Directory Tool ---

class CreateDirInput(BaseModel):
    """Input parameters for the create directory tool."""
    path: str = Field(..., description="Directory path relative to workspace root")
    recursive: bool = Field(True, description="Create parent directories if they do not exist")


class CreateDirTool(BaseTool[FilesystemProvider]):
    """Tool that creates a directory within the workspace."""

    name: str = "create_dir"
    description: str = "Create a new directory inside the workspace boundary."
    input_schema: Type[BaseModel] = CreateDirInput

    async def execute(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        """Create the directory at verified path."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_path = self.provider.validate_path(path)
        try:
            safe_path.mkdir(parents=recursive, exist_ok=True)
            return {"path": path, "status": "success"}
        except Exception as e:
            raise ExecutionError(f"Failed to create directory '{path}': {e}") from e


# --- Copy Tool ---

class CopyInput(BaseModel):
    """Input parameters for the copy tool."""
    source: str = Field(..., description="Source path relative to workspace root")
    destination: str = Field(..., description="Destination path relative to workspace root")


class CopyTool(BaseTool[FilesystemProvider]):
    """Tool that copies a file within the workspace."""

    name: str = "copy"
    description: str = "Copy a file from one location to another inside the workspace."
    input_schema: Type[BaseModel] = CopyInput

    async def execute(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy the verified source file to the verified destination."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_source = self.provider.validate_path(source)
        safe_dest = self.provider.validate_path(destination)
        try:
            if not safe_source.is_file():
                raise FileNotFoundError(f"Source file not found: '{source}'")
            safe_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(safe_source, safe_dest)
            return {"source": source, "destination": destination, "status": "success"}
        except Exception as e:
            raise ExecutionError(f"Failed to copy '{source}' to '{destination}': {e}") from e


# --- Move Tool ---

class MoveInput(BaseModel):
    """Input parameters for the move tool."""
    source: str = Field(..., description="Source path relative to workspace root")
    destination: str = Field(..., description="Destination path relative to workspace root")


class MoveTool(BaseTool[FilesystemProvider]):
    """Tool that moves (renames) a file or directory within the workspace."""

    name: str = "move"
    description: str = "Move or rename a file or directory inside the workspace."
    input_schema: Type[BaseModel] = MoveInput

    async def execute(self, source: str, destination: str) -> Dict[str, Any]:
        """Move the verified source to the verified destination."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_source = self.provider.validate_path(source)
        safe_dest = self.provider.validate_path(destination)
        try:
            if not safe_source.exists():
                raise FileNotFoundError(f"Source not found: '{source}'")
            safe_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(safe_source), str(safe_dest))
            return {"source": source, "destination": destination, "status": "success"}
        except Exception as e:
            raise ExecutionError(f"Failed to move '{source}' to '{destination}': {e}") from e


# --- Exists Tool ---

class ExistsInput(BaseModel):
    """Input parameters for the exists tool."""
    path: str = Field(..., description="File or directory path relative to workspace root")


class ExistsTool(BaseTool[FilesystemProvider]):
    """Tool that checks whether a file or directory exists."""

    name: str = "exists"
    description: str = "Check whether a file or directory exists inside the workspace."
    input_schema: Type[BaseModel] = ExistsInput

    async def execute(self, path: str) -> Dict[str, Any]:
        """Return whether the verified path exists."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_path = self.provider.validate_path(path)
        return {"path": path, "exists": safe_path.exists(), "status": "success"}


# --- File Info Tool ---

class FileInfoInput(BaseModel):
    """Input parameters for the file info tool."""
    path: str = Field(..., description="File or directory path relative to workspace root")


class FileInfoTool(BaseTool[FilesystemProvider]):
    """Tool that returns metadata about a file or directory."""

    name: str = "file_info"
    description: str = "Return name, size, type, and modification time for a workspace path."
    input_schema: Type[BaseModel] = FileInfoInput

    async def execute(self, path: str) -> Dict[str, Any]:
        """Return metadata of the verified path."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_path = self.provider.validate_path(path)
        try:
            if not safe_path.exists():
                raise FileNotFoundError(f"Path not found: '{path}'")

            stat = safe_path.stat()
            modified_dt = datetime.fromtimestamp(stat.st_mtime).isoformat()
            created_dt = datetime.fromtimestamp(stat.st_ctime).isoformat()
            return {
                "path": path,
                "name": safe_path.name,
                "size": stat.st_size,
                "type": "directory" if safe_path.is_dir() else "file",
                "modified": modified_dt,
                "created": created_dt,
                "status": "success",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to get file info for '{path}': {e}") from e


# --- Search Tool ---

class SearchInput(BaseModel):
    """Input parameters for the search tool."""
    path: str = Field(".", description="Base directory path relative to workspace root")
    pattern: str = Field(..., description="Glob pattern to match against, e.g. '*.py' or '**/*.py'")
    recursive: bool = Field(True, description="Search subdirectories recursively")


class SearchTool(BaseTool[FilesystemProvider]):
    """Tool that searches for files matching a glob pattern."""

    name: str = "search"
    description: str = "Search the workspace for files matching a glob pattern and return relative paths."
    input_schema: Type[BaseModel] = SearchInput

    async def execute(self, path: str = ".", pattern: str = "**/*", recursive: bool = True) -> Dict[str, Any]:
        """Search for files under the verified base path."""
        if not self.provider:
            raise ProviderError("FilesystemProvider has not been assigned to this tool.")

        safe_path = self.provider.validate_path(path)
        try:
            if not safe_path.is_dir():
                raise NotADirectoryError(f"Directory not found or invalid: '{path}'")

            results: List[str] = []
            if recursive:
                matched = safe_path.rglob(pattern)
            else:
                matched = safe_path.glob(pattern)

            for entry in matched:
                rel_path = entry.relative_to(self.provider.workspace_root)
                results.append(rel_path.as_posix())

            results.sort()
            return {
                "path": path,
                "pattern": pattern,
                "results": results,
                "count": len(results),
                "status": "success",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to search '{path}' for '{pattern}': {e}") from e
