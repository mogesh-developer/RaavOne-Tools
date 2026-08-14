"""Browser automation tools."""

from typing import Any, Dict, Literal, Optional, Type
from pydantic import BaseModel, Field

from raavone_tools.base import BaseTool
from raavone_tools.browser.provider import BrowserProvider
from raavone_tools.exceptions import ExecutionError, ProviderError


# --- Navigate Tool ---

class NavigateInput(BaseModel):
    """Input parameters for the navigate tool."""
    url: str = Field(..., description="The destination URL (must include HTTP/HTTPS protocol)")
    wait_until: str = Field(
        "load",
        description="Wait condition: 'load', 'domcontentloaded', or 'networkidle'",
    )


class NavigateTool(BaseTool[BrowserProvider]):
    """Tool that navigates the browser instance to a specified URL."""

    name: str = "navigate"
    description: str = "Navigate to a specific URL and return page details."
    input_schema: Type[BaseModel] = NavigateInput

    async def execute(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """Navigate to the target URL and wait for the page to load."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        # Map wait_until parameter
        playwright_wait = wait_until
        if playwright_wait not in {"load", "domcontentloaded", "networkidle", "commit"}:
            playwright_wait = "load"

        try:
            await page.goto(url, wait_until=playwright_wait)
            title = await page.title()
            return {
                "url": page.url,
                "title": title,
                "status": "success",
            }
        except Exception as e:
            raise ExecutionError(f"Navigation to {url} failed: {e}") from e


# --- Click Tool ---

class ClickInput(BaseModel):
    """Input parameters for the click tool."""
    selector: str = Field(..., description="CSS selector or XPath of the element to click")
    timeout: int = Field(10000, description="Max timeout in milliseconds to wait for the element")


class ClickTool(BaseTool[BrowserProvider]):
    """Tool that clicks an element matching a selector."""

    name: str = "click"
    description: str = "Click an element on the current page using a CSS or XPath selector."
    input_schema: Type[BaseModel] = ClickInput

    async def execute(self, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        """Find the selector and perform a click event."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            await page.click(selector, timeout=timeout)
            return {"status": "success", "message": f"Successfully clicked: '{selector}'"}
        except Exception as e:
            raise ExecutionError(f"Failed to click element '{selector}': {e}") from e


# --- Screenshot Tool ---

class ScreenshotInput(BaseModel):
    """Input parameters for the screenshot tool."""
    path: str = Field(..., description="Local filepath where screenshot will be saved")
    full_page: bool = Field(False, description="Capture full scrollable length of the page")


class ScreenshotTool(BaseTool[BrowserProvider]):
    """Tool that captures a page screenshot."""

    name: str = "screenshot"
    description: str = "Capture and save a screenshot of the current browser tab."
    input_schema: Type[BaseModel] = ScreenshotInput

    async def execute(self, path: str, full_page: bool = False) -> Dict[str, Any]:
        """Capture screenshot and write to filesystem."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            await page.screenshot(path=path, full_page=full_page)
            return {"status": "success", "path": path}
        except Exception as e:
            raise ExecutionError(f"Failed to capture screenshot: {e}") from e


# --- Scroll Tool ---

class ScrollInput(BaseModel):
    """Input parameters for the scroll tool."""
    direction: Literal["up", "down"] = Field("down", description="Direction to scroll: 'up' or 'down'")
    amount: Optional[int] = Field(500, description="Amount of pixels to scroll (ignored if selector is provided)")
    selector: Optional[str] = Field(None, description="CSS or XPath selector of the element to scroll into view")


class ScrollTool(BaseTool[BrowserProvider]):
    """Tool that scrolls the browser page."""

    name: str = "scroll"
    description: str = "Scroll the page up/down or to a specific element."
    input_schema: Type[BaseModel] = ScrollInput

    async def execute(
        self,
        direction: Literal["up", "down"] = "down",
        amount: Optional[int] = 500,
        selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform scroll on the current page."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            if selector:
                locator = page.locator(selector)
                await locator.scroll_into_view_if_needed()
                return {
                    "status": "success",
                    "message": f"Successfully scrolled to element: '{selector}'",
                }
            else:
                scroll_amount = amount if amount is not None else 500
                delta = scroll_amount if direction == "down" else -scroll_amount
                await page.evaluate(f"window.scrollBy(0, {delta})")
                return {
                    "status": "success",
                    "message": f"Successfully scrolled {direction} by {scroll_amount} pixels",
                }
        except Exception as e:
            raise ExecutionError(f"Failed to scroll: {e}") from e

