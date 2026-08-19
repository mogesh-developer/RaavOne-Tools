import os
import tempfile
import pytest

from raavone_tools.manager import ToolManager
from raavone_tools.http.provider import HttpProvider
from raavone_tools.http.tool import (
    HttpGetTool,
    HttpPostTool,
    HttpPutTool,
    HttpPatchTool,
    HttpDeleteTool,
    HttpDownloadTool,
)


@pytest.mark.asyncio
async def test_http_tools_live():
    manager = ToolManager()
    provider = HttpProvider()
    
    # Register all tools
    manager.register_tool(HttpGetTool(provider=provider))
    manager.register_tool(HttpPostTool(provider=provider))
    manager.register_tool(HttpPutTool(provider=provider))
    manager.register_tool(HttpPatchTool(provider=provider))
    manager.register_tool(HttpDeleteTool(provider=provider))
    manager.register_tool(HttpDownloadTool(provider=provider))
    
    await manager.initialize_providers()
    
    try:
        # 1. GET Request
        res_get = await manager.execute(
            "http_get", 
            {"url": "https://jsonplaceholder.typicode.com/posts/1"}
        )
        assert res_get["status_code"] == 200
        assert res_get["json"] is not None
        assert res_get["json"]["id"] == 1

        # 2. POST Request
        res_post = await manager.execute(
            "http_post", 
            {
                "url": "https://jsonplaceholder.typicode.com/posts",
                "json": {"title": "foo", "body": "bar", "userId": 1}
            }
        )
        assert res_post["status_code"] == 201
        assert res_post["json"] is not None
        assert res_post["json"]["title"] == "foo"

        # 3. PUT Request
        res_put = await manager.execute(
            "http_put", 
            {
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "json": {"id": 1, "title": "updated title", "body": "bar", "userId": 1}
            }
        )
        assert res_put["status_code"] == 200
        assert res_put["json"] is not None
        assert res_put["json"]["title"] == "updated title"

        # 4. PATCH Request
        res_patch = await manager.execute(
            "http_patch", 
            {
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "json": {"title": "patched title"}
            }
        )
        assert res_patch["status_code"] == 200
        assert res_patch["json"] is not None
        assert res_patch["json"]["title"] == "patched title"

        # 5. DELETE Request
        res_delete = await manager.execute(
            "http_delete", 
            {"url": "https://jsonplaceholder.typicode.com/posts/1"}
        )
        assert res_delete["status_code"] in (200, 202, 204)

        # 6. DOWNLOAD Request
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_file = os.path.join(tmpdir, "test_download.txt")
            res_download = await manager.execute(
                "http_download", 
                {
                    "url": "https://jsonplaceholder.typicode.com/todos/1",
                    "dest_path": dest_file
                }
            )
            assert res_download["status_code"] == 200
            assert res_download["status"] == "success"
            assert os.path.exists(dest_file)
            assert os.path.getsize(dest_file) > 0

    finally:
        await manager.close_providers()
