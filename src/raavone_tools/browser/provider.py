"""Browser resource provider utilizing Playwright."""

import logging
from typing import Any, Optional

from raavone_tools.base import BaseProvider
from raavone_tools.exceptions import ProviderError

logger = logging.getLogger(__name__)


class BrowserProvider(BaseProvider):
    """Resource provider that manages Playwright browser lifecycle and page contexts."""

    def __init__(self, headless: bool = True) -> None:
        """Initialize the browser provider configuration."""
        self.headless = headless
        self._playwright: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._context: Optional[Any] = None
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
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
            logger.info("Playwright browser initialized successfully.")
        except Exception as e:
            await self.close()
            raise ProviderError(f"Failed to initialize browser session: {e}") from e

    async def close(self) -> None:
        """Close browser pages, context, and stop the Playwright runner."""
        if self._page:
            try:
                await self._page.close()
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
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
