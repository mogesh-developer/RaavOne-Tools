import pytest

from raavone_tools.manager import ToolManager
from raavone_tools.search.provider import SearchProvider
from raavone_tools.search.tool import WebSearchTool


@pytest.mark.asyncio
async def test_web_search_workflow():
    manager = ToolManager()
    provider = SearchProvider()
    
    manager.register_tool(WebSearchTool(provider=provider))
    await manager.initialize_providers()
    
    try:
        res = await manager.execute("web_search", {"query": "Python programming", "max_results": 3})
        
        assert res["status"] == "success"
        assert res["query"] == "Python programming"
        assert isinstance(res["results"], list)
        
        # If there are results, check structure of the first item
        if len(res["results"]) > 0:
            first_res = res["results"][0]
            assert "title" in first_res
            assert "url" in first_res
            assert "snippet" in first_res
        
    finally:
        await manager.close_providers()
