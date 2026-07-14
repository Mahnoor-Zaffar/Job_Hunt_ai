import logging

from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    async_playwright,
)

from backend.scrapers.exceptions import BrowserError

logger = logging.getLogger("job_hunting.browser")


class BrowserManager:
    """Shared Playwright browser manager.

    Maintains a single browser instance and a shared context to reduce
    memory and speed up page creation.  All scrapers use the same
    browser instance.
    """

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self, headless: bool = True) -> None:
        if self._browser is not None:
            return
        try:
            self._playwright = await async_playwright().start()
            chromium: BrowserType = self._playwright.chromium
            self._browser = await chromium.launch(headless=headless)
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            logger.info("Browser launched (headless=%s)", headless)
        except Exception as exc:
            raise BrowserError(f"Failed to launch browser: {exc}", source="browser") from exc

    async def get_page(self) -> Page:
        if self._browser is None:
            await self.start()
        return await self._context.new_page()  # type: ignore[union-attr]

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser shut down")

    @property
    def is_running(self) -> bool:
        return self._browser is not None
