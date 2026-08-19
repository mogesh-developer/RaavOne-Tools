import os
import tempfile
from pathlib import Path
import pytest

from raavone_tools.manager import ToolManager
from raavone_tools.browser.provider import BrowserProvider
from raavone_tools.browser.tool import NavigateTool, ClickTool, ScreenshotTool, ScrollTool, ExtractTool


async def get_browser_manager():
    """Helper to initialize and return a registered ToolManager."""
    manager = ToolManager()
    provider = BrowserProvider(headless=True)
    manager.register_tool(NavigateTool(provider=provider))
    manager.register_tool(ClickTool(provider=provider))
    manager.register_tool(ScreenshotTool(provider=provider))
    manager.register_tool(ScrollTool(provider=provider))
    manager.register_tool(ExtractTool(provider=provider))
    await manager.initialize_providers()
    return manager


@pytest.mark.asyncio
async def test_extract_links():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = await get_browser_manager()
    try:
        # Navigate to a simple HTML with links
        await manager.execute(
            "navigate",
            {"url": 'data:text/html,<a href="https://example.com">Example Link</a>'}
        )
        res = await manager.execute("extract", {"mode": "links"})
        assert res["status"] == "success"
        assert len(res["data"]) == 1
        assert res["data"][0]["text"] == "Example Link"
        assert res["data"][0]["href"] == "https://example.com"
    finally:
        await manager.close_providers()


@pytest.mark.asyncio
async def test_extract_text():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = await get_browser_manager()
    try:
        await manager.execute(
            "navigate",
            {"url": 'data:text/html,<div id="content">Hello World</div>'}
        )
        # Without selector (whole page text)
        res = await manager.execute("extract", {"mode": "text"})
        assert "Hello World" in res["data"]
        
        # With selector
        res_sel = await manager.execute("extract", {"mode": "text", "selector": "#content"})
        assert res_sel["data"] == ["Hello World"]
    finally:
        await manager.close_providers()


@pytest.mark.asyncio
async def test_extract_html():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = await get_browser_manager()
    try:
        await manager.execute(
            "navigate",
            {"url": 'data:text/html,<div id="content"><span>Hello HTML</span></div>'}
        )
        # With selector
        res = await manager.execute("extract", {"mode": "html", "selector": "#content"})
        assert "<span>Hello HTML</span>" in res["data"][0]
    finally:
        await manager.close_providers()


@pytest.mark.asyncio
async def test_extract_elements():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = await get_browser_manager()
    try:
        await manager.execute(
            "navigate",
            {"url": 'data:text/html,<div class="project-card" data-id="123">RaavOne Minds</div>'}
        )
        res = await manager.execute("extract", {"mode": "elements", "selector": ".project-card"})
        assert res["status"] == "success"
        assert len(res["data"]) == 1
        assert res["data"][0]["tag"] == "div"
        assert res["data"][0]["text"] == "RaavOne Minds"
        assert res["data"][0]["attributes"]["data-id"] == "123"
    finally:
        await manager.close_providers()


@pytest.mark.asyncio
async def test_extract_table():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = await get_browser_manager()
    try:
        html_table = (
            "data:text/html,"
            "<table>"
            "  <tr><th>Name</th><th>Level</th></tr>"
            "  <tr><td>Python</td><td>Advanced</td></tr>"
            "</table>"
        )
        await manager.execute("navigate", {"url": html_table})
        res = await manager.execute("extract", {"mode": "tables"})
        assert res["status"] == "success"
        tables = res["data"]
        assert len(tables) == 1
        # Check headers and rows
        assert tables[0][0] == ["Name", "Level"]
        assert tables[0][1] == ["Python", "Advanced"]
    finally:
        await manager.close_providers()


@pytest.mark.asyncio
async def test_browser_tools():
    # Only run browser tests if playwright is available and installed
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = ToolManager()
    provider = BrowserProvider(headless=True)
    manager.register_tool(NavigateTool(provider=provider))
    manager.register_tool(ClickTool(provider=provider))
    manager.register_tool(ScreenshotTool(provider=provider))
    manager.register_tool(ScrollTool(provider=provider))
    manager.register_tool(ExtractTool(provider=provider))

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


@pytest.mark.asyncio
async def test_portfolio_extraction():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = ToolManager()
    provider = BrowserProvider(headless=True)
    manager.register_tool(NavigateTool(provider=provider))
    manager.register_tool(ExtractTool(provider=provider))

    await manager.initialize_providers()

    try:
        # Navigate to the live portfolio site
        nav_res = await manager.execute(
            "navigate",
            {"url": "https://mogeshdev.vercel.app/", "wait_until": "networkidle"}
        )
        assert nav_res["status"] == "success"

        # Extract Links
        extract_links = await manager.execute(
            "extract",
            {"mode": "links"}
        )
        assert extract_links["status"] == "success"
        links = extract_links["data"]
        assert len(links) > 0
        
        # Verify Github links exist
        github_links = [l for l in links if l.get("href") and "github.com/mogesh-developer" in l["href"]]
        assert len(github_links) > 0

    finally:
        await manager.close_providers()
