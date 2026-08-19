"""Database resource provider managing SQLite workspace safety boundaries and executions."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import SecurityValidationError, ExecutionError


class DatabaseProvider(BaseProvider):
    """Resource provider that interfaces safely with SQLite databases within workspace boundaries."""

    def __init__(self, workspace_root: Union[str, Path]) -> None:
        """Initialize database provider with target workspace root."""
        self.workspace_root = Path(workspace_root).resolve()

    async def initialize(self) -> None:
        """Ensure workspace root exists."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """No persistent pool resources required for sqlite."""
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

    def execute_sql(self, db_path: Path, sql: str, params: Union[List[Any], Dict[str, Any], Tuple[Any, ...]] = ()) -> Tuple[List[Dict[str, Any]], int, int]:
        """Execute a query synchronously and return fetched rows, lastrowid, and affected row count."""
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql, params)
            rows = []
            if cursor.description:
                rows = [dict(row) for row in cursor.fetchall()]
            conn.commit()
            return rows, cursor.lastrowid, cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise ExecutionError(f"Database execution failed: {e}") from e
        finally:
            cursor.close()
            conn.close()
