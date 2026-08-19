"""Browser resource provider utilizing Playwright."""

import logging
from pathlib import Path
from typing import Any, List, Optional, Union

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import ProviderError, SecurityValidationError

logger = logging.getLogger(__name__)


class BrowserProvider(BaseProvider):
    """Resource provider that manages Playwright browser lifecycle and page contexts."""

    def __init__(self, headless: bool = True, workspace_root: Optional[Union[str, Path]] = None) -> None:
        """Initialize the browser provider configuration."""
        self.headless = headless
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else None
        self._playwright: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._context: Optional[Any] = None
        self._pages: List[Any] = []
        self._page: Optional[Any] = None

    async def initialize(self) -> None:
        """Initialize the Playwright runner, browser and context."""
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise ProviderError(
                "Playwright is not installed. Please install it using: "
                "pip install -e .[browser] && playwright install"
            ) from e

        try:
            logger.info("Starting Playwright driver...")
            self._playwright = await async_playwright().start()
            logger.info("Launching chromium browser...")
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            self._context = await self._browser.new_context(accept_downloads=True)
            self._pages = []
            self._page = await self._context.new_page()
            self._pages.append(self._page)
            logger.info("Playwright browser initialized successfully.")
        except Exception as e:
            await self.close()
            raise ProviderError(f"Failed to initialize browser session: {e}") from e

    async def close(self) -> None:
        """Close all browser pages, context, and stop the Playwright runner."""
        for page in list(self._pages):
            try:
                await page.close()
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
        self._pages = []
        self._page = None

        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping Playwright: {e}")
            self._playwright = None

    async def get_page(self) -> Any:
        """Retrieve the active page instance, initializing the browser if necessary."""
        if self._page is None:
            await self.initialize()
        return self._page

    async def get_context(self) -> Any:
        """Retrieve the browser context, initializing the browser if necessary."""
        if self._context is None:
            await self.initialize()
        return self._context

    async def list_pages(self) -> List[Any]:
        """Return all open page instances."""
        if self._context is None:
            await self.initialize()
        return list(self._pages)

    async def new_page(self, url: Optional[str] = None) -> Any:
        """Create a new tab, make it active, and optionally navigate it."""
        context = await self.get_context()
        page = await context.new_page()
        self._pages.append(page)
        self._page = page
        if url:
            try:
                await page.goto(url, wait_until="load")
            except Exception as e:
                raise ProviderError(f"Failed to navigate new tab to {url}: {e}") from e
        return page

    async def switch_active_page(self, page: Any) -> None:
        """Set the given page as the active page."""
        self._page = page

    async def close_page(self, page: Any) -> None:
        """Close the given page and reselect an active tab."""
        if len(self._pages) <= 1:
            raise ProviderError("Cannot close the last open tab.")

        if page in self._pages:
            self._pages.remove(page)
        else:
            # Not part of our tracking; still try to close it.
            self._pages = [p for p in self._pages if p is not page]

        await page.close()

        if self._page is page or self._page is None:
            self._page = self._pages[-1] if self._pages else None

    def validate_dest_path(self, target_path: Union[str, Path]) -> Path:
        """Resolve a destination path, enforcing the workspace boundary when configured."""
        resolved = Path(target_path).expanduser().resolve()

        if self.workspace_root is not None:
            try:
                resolved.relative_to(self.workspace_root)
            except ValueError as e:
                raise SecurityValidationError(
                    f"Security Validation Error: Path '{target_path}' lies outside "
                    f"workspace boundary '{self.workspace_root}'."
                ) from e

        return resolved