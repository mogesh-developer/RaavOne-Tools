import os
import tempfile
import pytest
from pathlib import Path

from raavone_tools.manager import ToolManager
from raavone_tools.database.provider import DatabaseProvider
from raavone_tools.database.tool import (
    DbQueryTool,
    DbExecuteTool,
    DbTablesTool,
    DbSchemaTool,
)
from raavone_tools.exceptions import ExecutionError, SecurityValidationError


@pytest.mark.asyncio
async def test_database_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_root = Path(tmpdir)
        manager = ToolManager()
        provider = DatabaseProvider(workspace_root=workspace_root)
        
        manager.register_tool(DbQueryTool(provider=provider))
        manager.register_tool(DbExecuteTool(provider=provider))
        manager.register_tool(DbTablesTool(provider=provider))
        manager.register_tool(DbSchemaTool(provider=provider))
        
        await manager.initialize_providers()
        
        try:
            db_path = "test.db"
            
            # 1. Create table
            create_sql = "CREATE TABLE projects (id INTEGER PRIMARY KEY, title TEXT, stars INTEGER);"
            res_create = await manager.execute("db_execute", {"db_path": db_path, "sql": create_sql})
            assert res_create["status"] == "success"

            # 2. Insert records
            insert_sql = "INSERT INTO projects (title, stars) VALUES (?, ?);"
            res_insert1 = await manager.execute("db_execute", {
                "db_path": db_path,
                "sql": insert_sql,
                "params": ["RaavOne", 150]
            })
            assert res_insert1["status"] == "success"
            assert res_insert1["last_row_id"] == 1

            await manager.execute("db_execute", {
                "db_path": db_path,
                "sql": insert_sql,
                "params": ["AMC-Bot", 80]
            })

            # 3. Query tables list
            res_tables = await manager.execute("db_tables", {"db_path": db_path})
            assert res_tables["status"] == "success"
            assert "projects" in res_tables["tables"]

            # 4. Query table schema
            res_schema = await manager.execute("db_schema", {"db_path": db_path, "table_name": "projects"})
            assert res_schema["status"] == "success"
            assert len(res_schema["columns"]) == 3
            col_names = {c["name"] for c in res_schema["columns"]}
            assert "title" in col_names
            assert "stars" in col_names

            # 5. Query records
            query_sql = "SELECT * FROM projects WHERE stars > ? ORDER BY stars DESC;"
            res_query = await manager.execute("db_query", {
                "db_path": db_path,
                "sql": query_sql,
                "params": [50]
            })
            assert res_query["status"] == "success"
            assert res_query["count"] == 2
            assert res_query["rows"][0]["title"] == "RaavOne"
            assert res_query["rows"][0]["stars"] == 150

            # 6. Security Check: path outside boundary
            with pytest.raises(ExecutionError) as exc_info:
                await manager.execute("db_tables", {"db_path": "../outside.db"})
            assert "Security Validation Error" in str(exc_info.value)

            # 7. Security Check: Invalid table name SQL injection
            with pytest.raises(ExecutionError) as exc_info2:
                await manager.execute("db_schema", {"db_path": db_path, "table_name": "projects; DROP TABLE projects"})
            assert "Security ValidationError" in str(exc_info2.value)

        finally:
            await manager.close_providers()
