"""Database resource providers managing SQLite and defining multi-provider database schemas."""

import sqlite3
import asyncio
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import SecurityValidationError, ExecutionError


class BaseDatabaseProvider(BaseProvider):
    """Abstract base database provider defining the standard interface for SQL databases."""

    @abstractmethod
    async def query(self, sql: str, params: List[Any] = []) -> List[Dict[str, Any]]:
        """Run SQL SELECT query and return list of row dictionaries."""
        pass

    @abstractmethod
    async def execute(self, sql: str, params: List[Any] = []) -> Tuple[int, int]:
        """Run database update/insert execution and return (lastrowid, rowcount)."""
        pass

    @abstractmethod
    async def list_tables(self) -> List[str]:
        """Return a list of user tables existing inside the database."""
        pass

    @abstractmethod
    async def get_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Return the column metadata list for the specified table."""
        pass


class SQLiteProvider(BaseDatabaseProvider):
    """Concrete SQLite database provider implementing standard SQL abstractions."""

    def __init__(self, workspace_root: Union[str, Path], db_path: str) -> None:
        """Initialize SQLite provider and validate target database path."""
        self.workspace_root = Path(workspace_root).resolve()
        # Resolve target database path within workspace boundaries
        self.db_path = self.validate_path(db_path)

    async def initialize(self) -> None:
        """Ensure parent directories exist."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        """No persistent pool resources required for SQLite."""
        pass

    def validate_path(self, target_path: Union[str, Path]) -> Path:
        """Resolve database path and verify workspace boundary constraint."""
        path_obj = Path(target_path)
        
        # If relative, resolve relative to workspace_root
        if not path_obj.is_absolute():
            resolved = (self.workspace_root / path_obj).resolve()
        else:
            resolved = path_obj.resolve()

        # Check relative boundary match
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as e:
            raise SecurityValidationError(
                f"Security Validation Error: Path '{target_path}' lies outside "
                f"workspace boundary '{self.workspace_root}'."
            ) from e

        return resolved

    def _execute_sync(self, sql: str, params: List[Any]) -> Tuple[List[Dict[str, Any]], int, int]:
        """Execute a query synchronously and return rows list, lastrowid, and rowcount."""
        conn = sqlite3.connect(str(self.db_path))
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

    async def query(self, sql: str, params: List[Any] = []) -> List[Dict[str, Any]]:
        """Query rows asynchronously."""
        loop = asyncio.get_running_loop()
        rows, _, _ = await loop.run_in_executor(
            None,
            self._execute_sync,
            sql,
            params
        )
        return rows

    async def execute(self, sql: str, params: List[Any] = []) -> Tuple[int, int]:
        """Execute updates/inserts asynchronously."""
        loop = asyncio.get_running_loop()
        _, lastrowid, rowcount = await loop.run_in_executor(
            None,
            self._execute_sync,
            sql,
            params
        )
        return lastrowid, rowcount

    async def list_tables(self) -> List[str]:
        """Retrieve user tables from master catalogs."""
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        rows = await self.query(sql, [])
        return [row["name"] for row in rows]

    async def get_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Return the column metadata list for the specified table."""
        if not table_name or not table_name.isidentifier():
            raise SecurityValidationError(
                f"Security Validation Error: Invalid table name '{table_name}'"
            )
        rows = await self.query(f"PRAGMA table_info({table_name})", [])
        return [
            {
                "cid": row.get("cid"),
                "name": row.get("name"),
                "type": row.get("type"),
                "notnull": row.get("notnull"),
                "default": row.get("dflt_value"),
                "primary_key": row.get("pk"),
            }
            for row in rows
        ]

    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        # Using execute to run BEGIN; no params needed
        await self.execute('BEGIN', [])

    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        await self.execute('COMMIT', [])

    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        await self.execute('ROLLBACK', [])

    async def db_info(self) -> Dict[str, Any]:
        """Return basic information about the SQLite database."""
        # Get SQLite version
        version_rows = await self.query('SELECT sqlite_version() AS version', [])
        version = version_rows[0].get('version') if version_rows else 'unknown'
        # File size
        size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
        # Table count
        tables = await self.list_tables()
        return {
            'type': 'sqlite',
            'version': version,
            'size_bytes': size_bytes,
            'tables': len(tables),
            'table_names': tables,
        }
