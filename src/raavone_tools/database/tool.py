"""Database execution tools interacting with generic SQL base providers."""

from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.exceptions import ExecutionError, ProviderError
from raavone_tools.database.provider import BaseDatabaseProvider


# --- Database Query Tool ---

class DbQueryInput(BaseModel):
    """Input parameters for database select query."""
    sql: str = Field(..., description="SQL SELECT query string (must use ? or appropriate placeholders for arguments)")
    params: List[Any] = Field(default=[], description="Positional query parameters to bind to placeholders")


class DbQueryTool(BaseTool[BaseDatabaseProvider]):
    """Tool that queries a database and returns rows."""

    name: str = "db_query"
    description: str = "Query the database with a SELECT statement using parameterized bindings."
    input_schema: Type[BaseModel] = DbQueryInput

    async def execute(self, sql: str, params: List[Any] = []) -> Dict[str, Any]:
        """Perform query through the configured provider."""
        if not self.provider:
            raise ProviderError("Database provider has not been assigned to this tool.")

        # Basic read-only keyword verification
        sql_stripped = sql.strip().upper()
        if not (sql_stripped.startswith("SELECT") or sql_stripped.startswith("WITH") or sql_stripped.startswith("PRAGMA")):
            raise ExecutionError("db_query only supports SELECT, WITH, or PRAGMA commands. Use db_execute for write operations.")

        rows = await self.provider.query(sql, params)
        return {
            "status": "success",
            "rows": rows,
            "count": len(rows)
        }


# --- Database Execute Tool ---

class DbExecuteInput(BaseModel):
    """Input parameters for database modification query."""
    sql: str = Field(..., description="SQL command string (CREATE, INSERT, UPDATE, DELETE, etc.)")
    params: List[Any] = Field(default=[], description="Positional parameters to bind to placeholders")


class DbExecuteTool(BaseTool[BaseDatabaseProvider]):
    """Tool that executes updates, inserts, deletions, or schemas on the database."""

    name: str = "db_execute"
    description: str = "Execute an INSERT, UPDATE, DELETE, or CREATE statement on the database."
    input_schema: Type[BaseModel] = DbExecuteInput

    async def execute(self, sql: str, params: List[Any] = []) -> Dict[str, Any]:
        """Perform database execution through the provider."""
        if not self.provider:
            raise ProviderError("Database provider has not been assigned to this tool.")

        last_row_id, row_count = await self.provider.execute(sql, params)
        return {
            "status": "success",
            "last_row_id": last_row_id,
            "row_count": row_count
        }


# --- Database Tables Tool ---

class DbTablesInput(BaseModel):
    """Input parameters for listing tables (empty schema)."""
    pass


class DbTablesTool(BaseTool[BaseDatabaseProvider]):
    """Tool that lists tables inside the database."""

    name: str = "db_tables"
    description: str = "List all custom user tables inside the database."
    input_schema: Type[BaseModel] = DbTablesInput

    async def execute(self) -> Dict[str, Any]:
        """Fetch all table names through the provider."""
        if not self.provider:
            raise ProviderError("Database provider has not been assigned to this tool.")

        tables = await self.provider.list_tables()
        return {
            "status": "success",
            "tables": tables,
            "count": len(tables)
        }


# --- Database Schema Tool ---

class DbSchemaInput(BaseModel):
    """Input parameters for querying schema information."""
    table_name: str = Field(..., description="Table name identifier to query schemas for")


class DbSchemaTool(BaseTool[BaseDatabaseProvider]):
    """Tool that retrieves column layout schemas of a database table."""

    name: str = "db_schema"
    description: str = "Get columns, data types, nullability, and primary keys layout schema for a database table."
    input_schema: Type[BaseModel] = DbSchemaInput

    async def execute(self, table_name: str) -> Dict[str, Any]:
        """Perform schema discovery through the provider."""
        if not self.provider:
            raise ProviderError("Database provider has not been assigned to this tool.")

        columns = await self.provider.get_schema(table_name)
        return {
            "status": "success",
            "table": table_name,
            "columns": columns,
            "count": len(columns)
        }
