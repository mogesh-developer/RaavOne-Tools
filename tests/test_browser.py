import os
import tempfile
from pathlib import Path
import pytest

from raavone_tools.manager import ToolManager
from raavone_tools.browser.provider import BrowserProvider
from raavone_tools.exceptions import ExecutionError
from raavone_tools.browser.tool import (
    BackTool,
    ClearCookiesTool,
    ClickTool,
    CloseTabTool,
    DownloadTool,
    ExtractTool,
    FillTool,
    ForwardTool,
    GetAttributeTool,
    GetCookiesTool,
    HoverTool,
    ListTabsTool,
    NavigateTool,
    NewTabTool,
    PressTool,
    ReloadTool,
    ScreenshotTool,
    ScrollTool,
    SelectTool,
    SwitchTabTool,
    TypeTool,
    UploadTool,
    WaitForSelectorTool,
    WaitTool,
)


async def get_browser_manager():
    """Helper to initialize and return a registered ToolManager."""
    manager = ToolManager()
    provider = BrowserProvider(headless=True)
    manager.register_tool(NavigateTool(provider=provider))
    manager.register_tool(BackTool(provider=provider))
    manager.register_tool(ForwardTool(provider=provider))
    manager.register_tool(ReloadTool(provider=provider))
    manager.register_tool(ClickTool(provider=provider))
    manager.register_tool(FillTool(provider=provider))
    manager.register_tool(TypeTool(provider=provider))
    manager.register_tool(PressTool(provider=provider))
    manager.register_tool(SelectTool(provider=provider))
    manager.register_tool(HoverTool(provider=provider))
    manager.register_tool(WaitTool(provider=provider))
    manager.register_tool(WaitForSelectorTool(provider=provider))
    manager.register_tool(GetAttributeTool(provider=provider))
    manager.register_tool(NewTabTool(provider=provider))
    manager.register_tool(ListTabsTool(provider=provider))
    manager.register_tool(SwitchTabTool(provider=provider))
    manager.register_tool(CloseTabTool(provider=provider))
    manager.register_tool(DownloadTool(provider=provider))
    manager.register_tool(UploadTool(provider=provider))
    manager.register_tool(GetCookiesTool(provider=provider))
    manager.register_tool(ClearCookiesTool(provider=provider))
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
async def test_back_forward_reload():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = await get_browser_manager()
    try:
        page1 = "data:text/html,<h1>Page One</h1>"
        page2 = "data:text/html,<h1>Page Two</h1>"

        await manager.execute("navigate", {"url": page1})
        await manager.execute("navigate", {"url": page2})
        h1 = await manager.execute("extract", {"mode": "text", "selector": "h1"})
        assert h1["data"] == ["Page Two"]

        # Back to page one
        back_res = await manager.execute("back", {})
        assert back_res["status"] == "success"
        assert back_res["url"].startswith("data:")
        h1 = await manager.execute("extract", {"mode": "text", "selector": "h1"})
        assert h1["data"] == ["Page One"]

        # Forward back to page two
        fwd_res = await manager.execute("forward", {})
        assert fwd_res["status"] == "success"
        h1 = await manager.execute("extract", {"mode": "text", "selector": "h1"})
        assert h1["data"] == ["Page Two"]

        # Reload stays on page two
        reload_res = await manager.execute("reload", {})
        assert reload_res["status"] == "success"
        h1 = await manager.execute("extract", {"mode": "text", "selector": "h1"})
        assert h1["data"] == ["Page Two"]
    finally:
        await manager.close_providers()


@pytest.mark.asyncio
async def test_browser_interaction_tools():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = ToolManager()
    provider = BrowserProvider(headless=True)
    manager.register_tool(NavigateTool(provider=provider))
    manager.register_tool(FillTool(provider=provider))
    manager.register_tool(TypeTool(provider=provider))
    manager.register_tool(PressTool(provider=provider))
    manager.register_tool(SelectTool(provider=provider))
    manager.register_tool(HoverTool(provider=provider))
    manager.register_tool(WaitTool(provider=provider))
    manager.register_tool(WaitForSelectorTool(provider=provider))
    manager.register_tool(GetAttributeTool(provider=provider))
    manager.register_tool(ExtractTool(provider=provider))
    await manager.initialize_providers()

    try:
        # fill sets the input's value property
        await manager.execute(
            "navigate",
            {"url": "data:text/html,<input id='q' value=''>"}
        )
        await manager.execute("fill", {"selector": "#q", "value": "hello world"})
        page = await provider.get_page()
        assert await page.evaluate("document.getElementById('q').value") == "hello world"

        # get_attribute reads a real HTML attribute
        res = await manager.execute("get_attribute", {"selector": "#q", "attribute": "id"})
        assert res["status"] == "success"
        assert res["values"] == ["q"]

        # type appends into the input
        await manager.execute("type", {"selector": "#q", "text": "!!"})
        assert await page.evaluate("document.getElementById('q').value") == "hello world!!"

        # press Enter triggers the onkeydown handler
        page = await provider.get_page()
        await manager.execute(
            "navigate",
            {"url": (
                "data:text/html,"
                "<input id='k' onkeydown=\"if(event.key==='Enter'){"
                "document.getElementById('out').innerText='pressed'}\">"
                "<div id='out'></div>"
            )}
        )
        await manager.execute("press", {"selector": "#k", "key": "Enter"})
        res = await manager.execute("extract", {"mode": "text", "selector": "#out"})
        assert res["data"] == ["pressed"]

        # select option
        await manager.execute(
            "navigate",
            {"url": (
                "data:text/html,"
                "<select id='s'><option value='py'>Python</option>"
                "<option value='js'>Python</option></select>"
            )}
        )
        await manager.execute("select", {"selector": "#s", "value": "js"})
        page = await provider.get_page()
        selected = await page.evaluate("document.getElementById('s').value")
        assert selected == "js"

        # select by index
        await manager.execute("select", {"selector": "#s", "index": 0})
        selected = await page.evaluate("document.getElementById('s').value")
        assert selected == "py"

        # hover triggers mouseover handler
        await manager.execute(
            "navigate",
            {"url": (
                "data:text/html,"
                "<div id='h' onmouseover=\"document.getElementById('h').innerText='hovered'\">x</div>"
            )}
        )
        await manager.execute("hover", {"selector": "#h"})
        res = await manager.execute("extract", {"mode": "text", "selector": "#h"})
        assert res["data"] == ["hovered"]

        # wait_for_selector success + timeout
        await manager.execute(
            "navigate",
            {"url": "data:text/html,<div id='late'>content</div>"}
        )
        res = await manager.execute(
            "wait_for_selector", {"selector": "#late", "state": "visible", "timeout": 2000}
        )
        assert res["status"] == "success"

        with pytest.raises(ExecutionError) as exc_info:
            await manager.execute(
                "wait_for_selector", {"selector": "#never-appears", "timeout": 300}
            )
        assert "waiting for selector" in str(exc_info.value).lower() or "timeout" in str(exc_info.value).lower()

        # wait (load state)
        res = await manager.execute("wait", {"timeout": 2000, "state": "load"})
        assert res["status"] == "success"
    finally:
        await manager.close_providers()


@pytest.mark.asyncio
async def test_browser_tab_tools():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    manager = await get_browser_manager()
    try:
        await manager.execute("navigate", {"url": "data:text/html,<h1>One</h1>"})
        res = await manager.execute("new_tab", {"url": "data:text/html,<h1>Two</h1>"})
        assert res["status"] == "success"

        tabs = await manager.execute("list_tabs", {})
        assert tabs["count"] == 2
        assert any(t["active"] for t in tabs["tabs"])

        # Active tab is the new one
        h1 = await manager.execute("extract", {"mode": "text", "selector": "h1"})
        assert h1["data"] == ["Two"]

        # Switch by index
        res = await manager.execute("switch_tab", {"index": 0})
        assert res["status"] == "success"
        h1 = await manager.execute("extract", {"mode": "text", "selector": "h1"})
        assert h1["data"] == ["One"]

        # Switch by URL substring
        res = await manager.execute("switch_tab", {"url": "<h1>Two</h1>"})
        h1 = await manager.execute("extract", {"mode": "text", "selector": "h1"})
        assert h1["data"] == ["Two"]

        # Close active tab -> one tab remains
        res = await manager.execute("close_tab", {})
        assert res["status"] == "success"
        assert res["remaining_tabs"] == 1

        # Closing the last tab is blocked
        with pytest.raises(ExecutionError):
            await manager.execute("close_tab", {})
    finally:
        await manager.close_providers()


@pytest.mark.asyncio
async def test_browser_download_upload_cookies():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("Playwright not installed, skipping browser tests")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ToolManager()
        provider = BrowserProvider(headless=True, workspace_root=Path(tmpdir))
        manager.register_tool(NavigateTool(provider=provider))
        manager.register_tool(DownloadTool(provider=provider))
        manager.register_tool(UploadTool(provider=provider))
        manager.register_tool(GetCookiesTool(provider=provider))
        manager.register_tool(ClearCookiesTool(provider=provider))
        manager.register_tool(ExtractTool(provider=provider))
        await manager.initialize_providers()

        try:
            # download by URL
            out_path = os.path.join(tmpdir, "page.html")
            res = await manager.execute("download", {"url": "https://example.com", "path": out_path})
            assert res["status"] == "success"
            assert os.path.exists(out_path)
            assert os.path.getsize(out_path) > 0

            # upload to a file input
            upload_src = os.path.join(tmpdir, "upload.txt")
            with open(upload_src, "w") as f:
                f.write("upload payload")

            await manager.execute(
                "navigate",
                {"url": "data:text/html,<input id='f' type='file'>"}
            )
            res = await manager.execute("upload", {"selector": "#f", "path": upload_src})
            assert res["status"] == "success"
            page = await provider.get_page()
            name = await page.evaluate("document.getElementById('f').files[0].name")
            assert name == "upload.txt"

            # cookies: inject one, read, then clear
            await manager.execute("navigate", {"url": "https://example.com"})
            context = await provider.get_context()
            await context.add_cookies([{
                "name": "session_id",
                "value": "abc123",
                "domain": "example.com",
                "path": "/",
            }])
            res = await manager.execute("get_cookies", {})
            assert res["status"] == "success"
            assert res["count"] >= 1
            names = [c["name"] for c in res["cookies"]]
            assert "session_id" in names

            res = await manager.execute("clear_cookies", {})
            assert res["status"] == "success"
            res = await manager.execute("get_cookies", {})
            assert res["count"] == 0

            # download outside workspace is rejected
            with pytest.raises(ExecutionError) as exc_info:
                await manager.execute(
                    "download",
                    {"url": "https://example.com", "path": os.path.join(tmpdir, "..", "escape.html")},
                )
            assert "Security Validation Error" in str(exc_info.value)
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
    manager.register_tool(BackTool(provider=provider))
    manager.register_tool(ForwardTool(provider=provider))
    manager.register_tool(ReloadTool(provider=provider))
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
