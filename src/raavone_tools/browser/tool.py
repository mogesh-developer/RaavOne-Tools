"""Browser automation tools."""

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Type, Union
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


# --- Back Tool ---

class BackInput(BaseModel):
    """Input parameters for the back tool."""
    wait_until: str = Field(
        "load",
        description="Wait condition: 'load', 'domcontentloaded', or 'networkidle'",
    )


class BackTool(BaseTool[BrowserProvider]):
    """Tool that navigates the browser to the previous page in history."""

    name: str = "back"
    description: str = "Navigate to the previous page in the browser history."
    input_schema: Type[BaseModel] = BackInput

    async def execute(self, wait_until: str = "load") -> Dict[str, Any]:
        """Go back to the previous page in browser history."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        if wait_until not in {"load", "domcontentloaded", "networkidle", "commit"}:
            wait_until = "load"

        try:
            await page.go_back(wait_until=wait_until)
            title = await page.title()
            return {
                "url": page.url,
                "title": title,
                "status": "success",
                "message": "Navigated to the previous page.",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to navigate back: {e}") from e


# --- Forward Tool ---

class ForwardInput(BaseModel):
    """Input parameters for the forward tool."""
    wait_until: str = Field(
        "load",
        description="Wait condition: 'load', 'domcontentloaded', or 'networkidle'",
    )


class ForwardTool(BaseTool[BrowserProvider]):
    """Tool that navigates the browser to the next page in history."""

    name: str = "forward"
    description: str = "Navigate to the next page in the browser history."
    input_schema: Type[BaseModel] = ForwardInput

    async def execute(self, wait_until: str = "load") -> Dict[str, Any]:
        """Go forward to the next page in browser history."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        if wait_until not in {"load", "domcontentloaded", "networkidle", "commit"}:
            wait_until = "load"

        try:
            await page.go_forward(wait_until=wait_until)
            title = await page.title()
            return {
                "url": page.url,
                "title": title,
                "status": "success",
                "message": "Navigated to the next page.",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to navigate forward: {e}") from e


# --- Reload Tool ---

class ReloadInput(BaseModel):
    """Input parameters for the reload tool."""
    wait_until: str = Field(
        "load",
        description="Wait condition: 'load', 'domcontentloaded', or 'networkidle'",
    )


class ReloadTool(BaseTool[BrowserProvider]):
    """Tool that reloads the current page."""

    name: str = "reload"
    description: str = "Reload the current page in the browser."
    input_schema: Type[BaseModel] = ReloadInput

    async def execute(self, wait_until: str = "load") -> Dict[str, Any]:
        """Reload the current page."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        if wait_until not in {"load", "domcontentloaded", "networkidle", "commit"}:
            wait_until = "load"

        try:
            await page.reload(wait_until=wait_until)
            title = await page.title()
            return {
                "url": page.url,
                "title": title,
                "status": "success",
                "message": "Page reloaded.",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to reload page: {e}") from e


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


# --- Extract Tool ---

class ExtractInput(BaseModel):
    """Input parameters for the extract tool."""
    selector: Optional[str] = Field(None, description="CSS or XPath selector to scope/filter the extraction")
    mode: Literal["text", "html", "links", "images", "elements", "tables"] = Field(
        "text",
        description="Type of extraction: 'text', 'html', 'links', 'images', 'elements', 'tables'"
    )


class ExtractTool(BaseTool[BrowserProvider]):
    """Tool that extracts text or structured data from the current webpage."""

    name: str = "extract"
    description: str = "Extract page contents such as text, HTML, links, images, tables, or elements using selectors."
    input_schema: Type[BaseModel] = ExtractInput

    async def execute(
        self,
        selector: Optional[str] = None,
        mode: Literal["text", "html", "links", "images", "elements", "tables"] = "text",
    ) -> Dict[str, Any]:
        """Perform the extraction based on the selected mode and selector."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            if mode == "text":
                if selector:
                    locators = page.locator(selector)
                    count = await locators.count()
                    texts = [await locators.nth(i).inner_text() for i in range(count)]
                    return {"status": "success", "mode": mode, "data": texts}
                else:
                    text_content = await page.locator("body").inner_text()
                    return {"status": "success", "mode": mode, "data": text_content}

            elif mode == "html":
                if selector:
                    locators = page.locator(selector)
                    count = await locators.count()
                    htmls = [await locators.nth(i).inner_html() for i in range(count)]
                    return {"status": "success", "mode": mode, "data": htmls}
                else:
                    content = await page.content()
                    return {"status": "success", "mode": mode, "data": content}

            elif mode == "links":
                target_selector = f"{selector} a" if selector else "a"
                locators = page.locator(target_selector)
                count = await locators.count()
                links = []
                for i in range(count):
                    loc = locators.nth(i)
                    href = await loc.get_attribute("href")
                    text = await loc.inner_text()
                    links.append({"text": text.strip(), "href": href})
                return {"status": "success", "mode": mode, "data": links}

            elif mode == "images":
                target_selector = f"{selector} img" if selector else "img"
                locators = page.locator(target_selector)
                count = await locators.count()
                images = []
                for i in range(count):
                    loc = locators.nth(i)
                    src = await loc.get_attribute("src")
                    alt = await loc.get_attribute("alt") or ""
                    images.append({"src": src, "alt": alt})
                return {"status": "success", "mode": mode, "data": images}

            elif mode == "elements":
                if not selector:
                    raise ExecutionError("A selector must be provided when extracting elements.")
                locators = page.locator(selector)
                count = await locators.count()
                elements = []
                for i in range(count):
                    loc = locators.nth(i)
                    tag = await loc.evaluate("el => el.tagName.toLowerCase()")
                    text = await loc.inner_text()
                    # Extract attributes via JS
                    attrs = await loc.evaluate("""el => {
                        const attrs = {};
                        for (let attr of el.attributes) {
                            attrs[attr.name] = attr.value;
                        }
                        return attrs;
                    }""")
                    elements.append({
                        "tag": tag,
                        "text": text.strip(),
                        "attributes": attrs
                    })
                return {"status": "success", "mode": mode, "data": elements}

            elif mode == "tables":
                target_selector = f"{selector} table" if selector else "table"
                locators = page.locator(target_selector)
                count = await locators.count()
                tables = []
                for t in range(count):
                    table_loc = locators.nth(t)
                    rows = []
                    # Get all rows
                    row_locators = table_loc.locator("tr")
                    row_count = await row_locators.count()
                    for r in range(row_count):
                        row_loc = row_locators.nth(r)
                        # Find all headers or cells
                        cell_locators = row_loc.locator("th, td")
                        cell_count = await cell_locators.count()
                        cells = [await cell_locators.nth(c).inner_text() for c in range(cell_count)]
                        rows.append(cells)
                    tables.append(rows)
                return {"status": "success", "mode": mode, "data": tables}

            else:
                raise ExecutionError(f"Unsupported extraction mode: {mode}")

        except Exception as e:
            raise ExecutionError(f"Extraction failed: {e}") from e


# --- Fill Tool ---

class FillInput(BaseModel):
    """Input parameters for the fill tool."""
    selector: str = Field(..., description="CSS or XPath selector of the input to fill")
    value: str = Field(..., description="Text value to set into the input")
    timeout: int = Field(10000, description="Max timeout in milliseconds to wait for the element")


class FillTool(BaseTool[BrowserProvider]):
    """Tool that fills an input element with a value."""

    name: str = "fill"
    description: str = "Fill an input, textarea, or contenteditable with a value using a CSS or XPath selector."
    input_schema: Type[BaseModel] = FillInput

    async def execute(self, selector: str, value: str, timeout: int = 10000) -> Dict[str, Any]:
        """Fill the matching input element with value."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            await page.fill(selector, value, timeout=timeout)
            return {"status": "success", "message": f"Filled '{selector}' with the provided value."}
        except Exception as e:
            raise ExecutionError(f"Failed to fill element '{selector}': {e}") from e


# --- Type Tool ---

class TypeInput(BaseModel):
    """Input parameters for the type tool."""
    selector: str = Field(..., description="CSS or XPath selector of the element to type into")
    text: str = Field(..., description="Text to type character by character")
    delay: int = Field(0, description="Delay in milliseconds between keystrokes")
    timeout: int = Field(10000, description="Max timeout in milliseconds to wait for the element")


class TypeTool(BaseTool[BrowserProvider]):
    """Tool that types text into an element, simulating real keystrokes."""

    name: str = "type"
    description: str = "Type text into an element, simulating keystrokes, using a CSS or XPath selector."
    input_schema: Type[BaseModel] = TypeInput

    async def execute(
        self, selector: str, text: str, delay: int = 0, timeout: int = 10000
    ) -> Dict[str, Any]:
        """Type text into the matching element."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            await page.type(selector, text, delay=delay, timeout=timeout)
            return {"status": "success", "message": f"Typed text into '{selector}'."}
        except Exception as e:
            raise ExecutionError(f"Failed to type into element '{selector}': {e}") from e


# --- Press Tool ---

class PressInput(BaseModel):
    """Input parameters for the press tool."""
    key: str = Field(..., description="Key to press, e.g. 'Enter', 'Tab', 'Escape', 'Control+A'")
    selector: Optional[str] = Field(
        None,
        description="CSS or XPath selector of the element to press the key in (optional; uses focused element if omitted)",
    )
    timeout: int = Field(10000, description="Max timeout in milliseconds to wait for the element")


class PressTool(BaseTool[BrowserProvider]):
    """Tool that presses a keyboard key on an element or the focused element."""

    name: str = "press"
    description: str = "Press a keyboard key (e.g. Enter, Tab, Escape) on an element or the focused element."
    input_schema: Type[BaseModel] = PressInput

    async def execute(self, key: str, selector: Optional[str] = None, timeout: int = 10000) -> Dict[str, Any]:
        """Press the given key, optionally scoped to a selector."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            if selector:
                await page.press(selector, key, timeout=timeout)
            else:
                await page.keyboard.press(key)
            return {"status": "success", "message": f"Pressed key '{key}'."}
        except Exception as e:
            raise ExecutionError(f"Failed to press key '{key}': {e}") from e


# --- Select Tool ---

class SelectInput(BaseModel):
    """Input parameters for the select tool."""
    selector: str = Field(..., description="CSS or XPath selector of the <select> element")
    value: Optional[Union[str, List[str]]] = Field(None, description="Option value(s) to select")
    label: Optional[Union[str, List[str]]] = Field(None, description="Option label(s) to select")
    index: Optional[Union[int, List[int]]] = Field(None, description="Option index (0-based) to select")
    timeout: int = Field(10000, description="Max timeout in milliseconds to wait for the element")


class SelectTool(BaseTool[BrowserProvider]):
    """Tool that selects an option in a <select> dropdown."""

    name: str = "select"
    description: str = "Select an option in a <select> dropdown by value, label, or index."
    input_schema: Type[BaseModel] = SelectInput

    async def execute(
        self,
        selector: str,
        value: Optional[Union[str, List[str]]] = None,
        label: Optional[Union[str, List[str]]] = None,
        index: Optional[Union[int, List[int]]] = None,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """Select an option by value, label, or index."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            if value is not None:
                await page.select_option(selector, value=value, timeout=timeout)
            elif label is not None:
                await page.select_option(selector, label=label, timeout=timeout)
            elif index is not None:
                await page.select_option(selector, index=index, timeout=timeout)
            else:
                raise ExecutionError("Select requires one of: value, label, or index.")
            return {"status": "success", "message": f"Selected option in '{selector}'."}
        except Exception as e:
            raise ExecutionError(f"Failed to select option in '{selector}': {e}") from e


# --- Hover Tool ---

class HoverInput(BaseModel):
    """Input parameters for the hover tool."""
    selector: str = Field(..., description="CSS or XPath selector of the element to hover over")
    timeout: int = Field(10000, description="Max timeout in milliseconds to wait for the element")


class HoverTool(BaseTool[BrowserProvider]):
    """Tool that hovers the mouse over an element."""

    name: str = "hover"
    description: str = "Move the mouse pointer over an element using a CSS or XPath selector."
    input_schema: Type[BaseModel] = HoverInput

    async def execute(self, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        """Hover over the matching element."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            await page.hover(selector, timeout=timeout)
            return {"status": "success", "message": f"Hovered over '{selector}'."}
        except Exception as e:
            raise ExecutionError(f"Failed to hover over element '{selector}': {e}") from e


# --- Wait Tool ---

class WaitInput(BaseModel):
    """Input parameters for the wait tool."""
    timeout: int = Field(1000, description="Number of milliseconds to wait")
    state: Literal["load", "domcontentloaded", "networkidle"] = Field(
        "load",
        description="Page load state to wait for",
    )


class WaitTool(BaseTool[BrowserProvider]):
    """Tool that waits for a page load state or a fixed duration."""

    name: str = "wait"
    description: str = "Wait for a page load state ('load', 'domcontentloaded', 'networkidle') with a timeout."
    input_schema: Type[BaseModel] = WaitInput

    async def execute(
        self,
        timeout: int = 1000,
        state: Literal["load", "domcontentloaded", "networkidle"] = "load",
    ) -> Dict[str, Any]:
        """Wait for the requested load state or timeout."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            await page.wait_for_load_state(state, timeout=timeout)
            return {
                "status": "success",
                "message": f"Waited for load state '{state}' (up to {timeout}ms).",
            }
        except Exception as e:
            raise ExecutionError(f"Wait failed: {e}") from e


# --- Wait For Selector Tool ---

class WaitForSelectorInput(BaseModel):
    """Input parameters for the wait_for_selector tool."""
    selector: str = Field(..., description="CSS or XPath selector to wait for")
    state: Literal["visible", "hidden", "attached", "detached"] = Field(
        "visible",
        description="State to wait for: 'visible', 'hidden', 'attached', or 'detached'",
    )
    timeout: int = Field(30000, description="Max timeout in milliseconds to keep waiting")


class WaitForSelectorTool(BaseTool[BrowserProvider]):
    """Tool that waits for an element to reach a given state."""

    name: str = "wait_for_selector"
    description: str = "Wait for an element matching a selector to reach a state (e.g. visible)."
    input_schema: Type[BaseModel] = WaitForSelectorInput

    async def execute(
        self,
        selector: str,
        state: Literal["visible", "hidden", "attached", "detached"] = "visible",
        timeout: int = 30000,
    ) -> Dict[str, Any]:
        """Wait for the selector to reach the requested state."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            await page.wait_for_selector(selector, state=state, timeout=timeout)
            return {
                "status": "success",
                "message": f"Selector '{selector}' reached state '{state}'.",
            }
        except Exception as e:
            raise ExecutionError(f"Timed out waiting for selector '{selector}': {e}") from e


# --- Get Attribute Tool ---

class GetAttributeInput(BaseModel):
    """Input parameters for the get_attribute tool."""
    selector: str = Field(..., description="CSS or XPath selector of the element(s)")
    attribute: str = Field(..., description="Attribute name to read, e.g. 'href', 'src', 'class'")


class GetAttributeTool(BaseTool[BrowserProvider]):
    """Tool that reads an attribute value from one or more elements."""

    name: str = "get_attribute"
    description: str = "Read an attribute (e.g. href, src, class) from elements matching a selector."
    input_schema: Type[BaseModel] = GetAttributeInput

    async def execute(self, selector: str, attribute: str) -> Dict[str, Any]:
        """Return the attribute values of all matching elements."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        page = await self.provider.get_page()
        try:
            locators = page.locator(selector)
            count = await locators.count()
            values = []
            for i in range(count):
                value = await locators.nth(i).get_attribute(attribute)
                values.append(value)
            return {
                "status": "success",
                "selector": selector,
                "attribute": attribute,
                "values": values,
            }
        except Exception as e:
            raise ExecutionError(f"Failed to read attribute '{attribute}' from '{selector}': {e}") from e


# --- New Tab Tool ---

class NewTabInput(BaseModel):
    """Input parameters for the new tab tool."""
    url: Optional[str] = Field(None, description="Optional URL to open in the new tab")
    wait_until: str = Field(
        "load",
        description="Wait condition: 'load', 'domcontentloaded', or 'networkidle'",
    )


class NewTabTool(BaseTool[BrowserProvider]):
    """Tool that opens a new browser tab."""

    name: str = "new_tab"
    description: str = "Open a new tab, optionally navigating to a URL, and make it active."
    input_schema: Type[BaseModel] = NewTabInput

    async def execute(self, url: Optional[str] = None, wait_until: str = "load") -> Dict[str, Any]:
        """Open a new tab and switch focus to it."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        try:
            page = await self.provider.new_page(url=url)
            title = await page.title()
            return {
                "status": "success",
                "url": page.url,
                "title": title,
                "tab_index": len(await self.provider.list_pages()) - 1,
                "message": "Opened a new tab.",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to open a new tab: {e}") from e


# --- List Tabs Tool ---

class ListTabsInput(BaseModel):
    """Input parameters for the list tabs tool."""
    pass


class ListTabsTool(BaseTool[BrowserProvider]):
    """Tool that lists all open browser tabs."""

    name: str = "list_tabs"
    description: str = "List all open tabs with their index, URL, and title."
    input_schema: Type[BaseModel] = ListTabsInput

    async def execute(self) -> Dict[str, Any]:
        """Return details of all open tabs."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        try:
            pages = await self.provider.list_pages()
            active = await self.provider.get_page()
            tabs = []
            for index, page in enumerate(pages):
                try:
                    title = await page.title()
                except Exception:
                    title = ""
                tabs.append({
                    "index": index,
                    "url": page.url,
                    "title": title,
                    "active": page is active,
                })
            return {"status": "success", "count": len(tabs), "tabs": tabs}
        except Exception as e:
            raise ExecutionError(f"Failed to list tabs: {e}") from e


# --- Switch Tab Tool ---

class SwitchTabInput(BaseModel):
    """Input parameters for the switch tab tool."""
    index: Optional[int] = Field(None, description="Tab index to switch to (0-based)")
    url: Optional[str] = Field(None, description="Switch to the first tab whose URL contains this substring")


class SwitchTabTool(BaseTool[BrowserProvider]):
    """Tool that switches the active tab."""

    name: str = "switch_tab"
    description: str = "Switch the active tab by index or by URL substring."
    input_schema: Type[BaseModel] = SwitchTabInput

    async def execute(self, index: Optional[int] = None, url: Optional[str] = None) -> Dict[str, Any]:
        """Switch the active tab by index or URL match."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        try:
            pages = await self.provider.list_pages()
            if index is None and url is None:
                raise ExecutionError("switch_tab requires either 'index' or 'url'.")

            if index is not None:
                if index < 0 or index >= len(pages):
                    raise ExecutionError(f"Invalid tab index '{index}'. Open tabs: {len(pages)}")
                target = pages[index]
            else:
                target = next(
                    (p for p in pages if url and url in p.url),
                    None,
                )
                if target is None:
                    raise ExecutionError(f"No tab found with URL containing '{url}'.")

            await self.provider.switch_active_page(target)
            title = await target.title()
            return {
                "status": "success",
                "tab_index": pages.index(target),
                "url": target.url,
                "title": title,
                "message": f"Switched to tab at index {pages.index(target)}.",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to switch tab: {e}") from e


# --- Close Tab Tool ---

class CloseTabInput(BaseModel):
    """Input parameters for the close tab tool."""
    index: Optional[int] = Field(None, description="Tab index to close (defaults to the active tab)")


class CloseTabTool(BaseTool[BrowserProvider]):
    """Tool that closes a browser tab."""

    name: str = "close_tab"
    description: str = "Close a tab by index, or the active tab when no index is given."
    input_schema: Type[BaseModel] = CloseTabInput

    async def execute(self, index: Optional[int] = None) -> Dict[str, Any]:
        """Close the specified tab or the active tab."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        try:
            pages = await self.provider.list_pages()
            if index is None:
                target = await self.provider.get_page()
            else:
                if index < 0 or index >= len(pages):
                    raise ExecutionError(f"Invalid tab index '{index}'. Open tabs: {len(pages)}")
                target = pages[index]

            closed_index = pages.index(target)
            await self.provider.close_page(target)
            return {
                "status": "success",
                "closed_index": closed_index,
                "remaining_tabs": len(await self.provider.list_pages()),
                "message": f"Closed tab at index {closed_index}.",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to close tab: {e}") from e


# --- Download Tool ---

class DownloadInput(BaseModel):
    """Input parameters for the download tool."""
    path: str = Field(..., description="Destination file path to save the download to")
    url: Optional[str] = Field(None, description="URL to download from directly")
    selector: Optional[str] = Field(None, description="Selector of a link/button that triggers the download")
    timeout: int = Field(30000, description="Max timeout in milliseconds to wait for the download")


class DownloadTool(BaseTool[BrowserProvider]):
    """Tool that downloads a file via URL or by clicking an element."""

    name: str = "download"
    description: str = "Download a file from a URL or by clicking an element that triggers a download."
    input_schema: Type[BaseModel] = DownloadInput

    async def execute(
        self,
        path: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        timeout: int = 30000,
    ) -> Dict[str, Any]:
        """Download a file to the given path."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        if not url and not selector:
            raise ExecutionError("download requires either 'url' or 'selector'.")

        dest = self.provider.validate_dest_path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            if url:
                context = await self.provider.get_context()
                response = await context.request.get(url, timeout=timeout)
                if response.status >= 400:
                    raise ExecutionError(f"Download failed with HTTP {response.status}: {url}")
                body = await response.body()
                dest.write_bytes(body)
                return {
                    "status": "success",
                    "path": str(dest),
                    "bytes": len(body),
                    "method": "url",
                }

            page = await self.provider.get_page()
            async with page.expect_download(timeout=timeout) as dl_info:
                await page.click(selector, timeout=timeout)
            download = await dl_info.value
            await download.save_as(str(dest))
            return {
                "status": "success",
                "path": str(dest),
                "filename": download.suggested_filename,
                "method": "click",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to download: {e}") from e


# --- Upload Tool ---

class UploadInput(BaseModel):
    """Input parameters for the upload tool."""
    selector: str = Field(..., description="CSS or XPath selector of the file input element")
    path: Union[str, List[str]] = Field(..., description="Local file path(s) to upload")


class UploadTool(BaseTool[BrowserProvider]):
    """Tool that uploads a file to a file input element."""

    name: str = "upload"
    description: str = "Upload files to a file input element using a CSS or XPath selector."
    input_schema: Type[BaseModel] = UploadInput

    async def execute(self, selector: str, path: Union[str, List[str]]) -> Dict[str, Any]:
        """Set files on the given file input."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        paths = [path] if isinstance(path, str) else path
        for p in paths:
            if not Path(p).expanduser().is_file():
                raise ExecutionError(f"File to upload does not exist: '{p}'")

        page = await self.provider.get_page()
        try:
            await page.set_input_files(selector, paths)
            return {"status": "success", "message": f"Uploaded {len(paths)} file(s) to '{selector}'."}
        except Exception as e:
            raise ExecutionError(f"Failed to upload to '{selector}': {e}") from e


# --- Get Cookies Tool ---

class GetCookiesInput(BaseModel):
    """Input parameters for the get cookies tool."""
    urls: Optional[List[str]] = Field(None, description="Optional list of URLs to filter cookies by")


class GetCookiesTool(BaseTool[BrowserProvider]):
    """Tool that reads cookies from the browser context."""

    name: str = "get_cookies"
    description: str = "Return all cookies (optionally filtered by URL) from the browser context."
    input_schema: Type[BaseModel] = GetCookiesInput

    async def execute(self, urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """Return the cookies of the browser context."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        try:
            context = await self.provider.get_context()
            cookies = await context.cookies(urls if urls else None)
            return {"status": "success", "count": len(cookies), "cookies": cookies}
        except Exception as e:
            raise ExecutionError(f"Failed to get cookies: {e}") from e


# --- Clear Cookies Tool ---

class ClearCookiesInput(BaseModel):
    """Input parameters for the clear cookies tool."""
    pass


class ClearCookiesTool(BaseTool[BrowserProvider]):
    """Tool that clears all cookies from the browser context."""

    name: str = "clear_cookies"
    description: str = "Clear all cookies from the browser context."
    input_schema: Type[BaseModel] = ClearCookiesInput

    async def execute(self) -> Dict[str, Any]:
        """Clear all cookies in the browser context."""
        if not self.provider:
            raise ProviderError("BrowserProvider has not been assigned to this tool.")

        try:
            context = await self.provider.get_context()
            cookies = await context.cookies()
            await context.clear_cookies()
            return {
                "status": "success",
                "cleared": len(cookies),
                "message": f"Cleared {len(cookies)} cookie(s).",
            }
        except Exception as e:
            raise ExecutionError(f"Failed to clear cookies: {e}") from e


