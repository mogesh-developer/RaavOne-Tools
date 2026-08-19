"""Database execution tools."""

import asyncio
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.database.provider import DatabaseProvider


# --- Database Query Tool ---

class DbQueryInput(BaseModel):
    """Input parameters for database select query."""
    db_path: str = Field(..., description="Path to the SQLite database file relative to the workspace root")
    sql: str = Field(..., description="SQL SELECT query string (must use ? parameters for arguments)")
    params: List[Any] = Field(default=[], description="Positional query parameters to bind to placeholders")


class DbQueryTool(BaseTool[DatabaseProvider]):
    """Tool that queries a SQLite database and returns rows."""

    name: str = "db_query"
    description: str = "Query a SQLite database with a SELECT statement using parameterized bindings."
    input_schema: Type[BaseModel] = DbQueryInput

    async def execute(self, db_path: str, sql: str, params: List[Any] = []) -> Dict[str, Any]:
        """Perform database query in async thread executor."""
        if not self.provider:
            raise ProviderError("DatabaseProvider has not been assigned to this tool.")

        real_db = self.provider.validate_path(db_path)

        # Enforce that query starts with SELECT or similar read-only keywords
        sql_stripped = sql.strip().upper()
        if not (sql_stripped.startswith("SELECT") or sql_stripped.startswith("WITH") or sql_stripped.startswith("PRAGMA")):
            raise ExecutionError("db_query only supports SELECT, WITH, or PRAGMA commands. Use db_execute for write operations.")

        loop = asyncio.get_running_loop()
        rows, _, _ = await loop.run_in_executor(
            None,
            self.provider.execute_sql,
            real_db,
            sql,
            params
        )

        return {
            "status": "success",
            "rows": rows,
            "count": len(rows)
        }


# --- Database Execute Tool ---

class DbExecuteInput(BaseModel):
    """Input parameters for database modification query."""
    db_path: str = Field(..., description="Path to the SQLite database file relative to the workspace root")
    sql: str = Field(..., description="SQL command string (CREATE, INSERT, UPDATE, DELETE, etc.)")
    params: List[Any] = Field(default=[], description="Positional parameters to bind to placeholders")


class DbExecuteTool(BaseTool[DatabaseProvider]):
    """Tool that executes updates, inserts, deletions, or schemas on a SQLite database."""

    name: str = "db_execute"
    description: str = "Execute an INSERT, UPDATE, DELETE, or CREATE statement on a SQLite database."
    input_schema: Type[BaseModel] = DbExecuteInput

    async def execute(self, db_path: str, sql: str, params: List[Any] = []) -> Dict[str, Any]:
        """Perform database execution in thread executor."""
        if not self.provider:
            raise ProviderError("DatabaseProvider has not been assigned to this tool.")

        real_db = self.provider.validate_path(db_path)

        loop = asyncio.get_running_loop()
        _, last_row_id, row_count = await loop.run_in_executor(
            None,
            self.provider.execute_sql,
            real_db,
            sql,
            params
        )

        return {
            "status": "success",
            "last_row_id": last_row_id,
            "row_count": row_count
        }


# --- Database Tables Tool ---

class DbTablesInput(BaseModel):
    """Input parameters for listing tables."""
    db_path: str = Field(..., description="Path to the SQLite database file relative to the workspace root")


class DbTablesTool(BaseTool[DatabaseProvider]):
    """Tool that lists tables inside a SQLite database."""

    name: str = "db_tables"
    description: str = "List all custom user tables inside a SQLite database."
    input_schema: Type[BaseModel] = DbTablesInput

    async def execute(self, db_path: str) -> Dict[str, Any]:
        """Fetch all table names."""
        if not self.provider:
            raise ProviderError("DatabaseProvider has not been assigned to this tool.")

        real_db = self.provider.validate_path(db_path)
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"

        loop = asyncio.get_running_loop()
        rows, _, _ = await loop.run_in_executor(
            None,
            self.provider.execute_sql,
            real_db,
            sql,
            []
        )

        tables = [row["name"] for row in rows]
        return {
            "status": "success",
            "tables": tables,
            "count": len(tables)
        }


# --- Database Schema Tool ---

class DbSchemaInput(BaseModel):
    """Input parameters for querying schema information."""
    db_path: str = Field(..., description="Path to the SQLite database file relative to the workspace root")
    table_name: str = Field(..., description="Table name identifier to query schemas for")


class DbSchemaTool(BaseTool[DatabaseProvider]):
    """Tool that retrieves column layout schemas of a SQLite table."""

    name: str = "db_schema"
    description: str = "Get columns, data types, nullability, and primary keys layout schema for a database table."
    input_schema: Type[BaseModel] = DbSchemaInput

    async def execute(self, db_path: str, table_name: str) -> Dict[str, Any]:
        """Perform schema discovery safely preventing SQL injection on identifiers."""
        if not self.provider:
            raise ProviderError("DatabaseProvider has not been assigned to this tool.")

        # Strict validation: table names must be valid identifiers to prevent SQL injection in PRAGMA
        if not table_name.isidentifier():
            raise ExecutionError(f"Security ValidationError: Invalid table name identifier '{table_name}'.")

        real_db = self.provider.validate_path(db_path)
        sql = f"PRAGMA table_info({table_name});"

        loop = asyncio.get_running_loop()
        rows, _, _ = await loop.run_in_executor(
            None,
            self.provider.execute_sql,
            real_db,
            sql,
            []
        )

        columns = []
        for r in rows:
            columns.append({
                "column_id": r.get("cid"),
                "name": r.get("name"),
                "type": r.get("type"),
                "notnull": bool(r.get("notnull")),
                "default_value": r.get("dflt_value"),
                "pk": bool(r.get("pk"))
            })

        return {
            "status": "success",
            "table": table_name,
            "columns": columns,
            "count": len(columns)
        }
