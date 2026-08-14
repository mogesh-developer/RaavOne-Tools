import pytest
import os
import tempfile
from pathlib import Path
from raavone_tools.manager import ToolManager
from raavone_tools.browser.provider import BrowserProvider
from raavone_tools.browser.tool import NavigateTool, ClickTool, ScreenshotTool, ScrollTool

@pytest.mark.asyncio
async def test_browser_tools():
    # Only run browser tests if playwright is available and installed
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = ToolManager()
    # Use headless mode for testing
    provider = BrowserProvider(headless=True)
    
    # Register browser tools
    manager.register_tool(NavigateTool(provider=provider))
    manager.register_tool(ClickTool(provider=provider))
    manager.register_tool(ScreenshotTool(provider=provider))
    manager.register_tool(ScrollTool(provider=provider))

    # Initialize providers
    await manager.initialize_providers()

    try:
        # Navigate to a simple, fast webpage (e.g. example.com)
        nav_result = await manager.execute(
            "navigate",
            {"url": "https://example.com"}
        )
        assert nav_result["status"] == "success"
        assert "Example Domain" in nav_result["title"]

        # Take a screenshot
        with tempfile.TemporaryDirectory() as tmpdir:
            shot_path = os.path.join(tmpdir, "screenshot.png")
            shot_result = await manager.execute(
                "screenshot",
                {"path": shot_path}
            )
            assert shot_result["status"] == "success"
            assert os.path.exists(shot_path)
            assert os.path.getsize(shot_path) > 0

        # Test scroll tool (down and up)
        scroll_down_result = await manager.execute(
            "scroll",
            {"direction": "down", "amount": 200}
        )
        assert scroll_down_result["status"] == "success"
        assert "scrolled down" in scroll_down_result["message"]

        scroll_up_result = await manager.execute(
            "scroll",
            {"direction": "up", "amount": 100}
        )
        assert scroll_up_result["status"] == "success"
        assert "scrolled up" in scroll_up_result["message"]

        # Test scroll into view using selector (body tag is always present)
        scroll_to_result = await manager.execute(
            "scroll",
            {"selector": "body"}
        )
        assert scroll_to_result["status"] == "success"
        assert "scrolled to element" in scroll_to_result["message"]
    finally:
        await manager.close_providers()
