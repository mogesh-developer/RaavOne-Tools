import pytest
from unittest.mock import patch

from raavone_tools.manager import ToolManager
from raavone_tools.search.provider import SearchProvider
from raavone_tools.search.tool import WebSearchTool


@pytest.mark.asyncio
async def test_web_search_workflow():
    manager = ToolManager()
    provider = SearchProvider()
    
    manager.register_tool(WebSearchTool(provider=provider))
    await manager.initialize_providers()
    
    mock_results = [
        {
            "title": "Welcome to Python.org",
            "url": "https://www.python.org/",
            "snippet": "The official home of the Python Programming Language"
        }
    ]
    
    with patch.object(provider, "search_text", return_value=mock_results):
        try:
            res = await manager.execute("web_search", {"query": "Python programming", "max_results": 3})
            
            assert res["status"] == "success"
            assert res["query"] == "Python programming"
            assert len(res["results"]) > 0
            assert res["results"][0]["title"] == "Welcome to Python.org"
            assert res["results"][0]["url"] == "https://www.python.org/"
            assert res["results"][0]["snippet"] == "The official home of the Python Programming Language"
            
        finally:
            await manager.close_providers()
