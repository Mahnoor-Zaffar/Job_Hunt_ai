"""Enhanced Browser Manager — context pool, session, cookie, auth, downloads.

Built on the existing Playwright singleton pattern but extended with
resource pooling, session persistence, cookie management, and
authentication handling for production ATS automation.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    async_playwright,
)

logger = logging.getLogger("job_hunting.automation")


class ContextPool:
    def __init__(self, max_contexts: int = 5) -> None:
        self._contexts: list[BrowserContext] = []
        self._max = max_contexts
        self._sem = asyncio.Semaphore(max_contexts)

    async def acquire(self, browser: Browser, **kwargs: Any) -> BrowserContext:
        await self._sem.acquire()
        ctx = await browser.new_context(**kwargs)
        self._contexts.append(ctx)
        return ctx

    async def release(self, ctx: BrowserContext) -> None:
        if ctx in self._contexts:
            await ctx.close()
            self._contexts.remove(ctx)
            self._sem.release()

    async def close_all(self) -> None:
        for ctx in list(self._contexts):
            await ctx.close()
        self._contexts.clear()


class PagePool:
    def __init__(self, max_pages: int = 10) -> None:
        self._pages: list[Page] = []
        self._max = max_pages

    async def acquire(self, context: BrowserContext) -> Page:
        page = await context.new_page()
        self._pages.append(page)
        return page

    async def release(self, page: Page) -> None:
        if page in self._pages:
            await page.close()
            self._pages.remove(page)

    async def close_all(self) -> None:
        for page in list(self._pages):
            await page.close()
        self._pages.clear()


class CookieManager:
    @staticmethod
    async def save(ctx: BrowserContext, path: str) -> None:
        cookies = await ctx.cookies()
        import json as json_mod

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json_mod.dumps(cookies), encoding="utf-8")

    @staticmethod
    async def load(ctx: BrowserContext, path: str) -> bool:
        try:
            import json as json_mod

            data = json_mod.loads(Path(path).read_text(encoding="utf-8"))
            await ctx.add_cookies(data)
            return True
        except (FileNotFoundError, json_mod.JSONDecodeError, Exception):
            return False


class AuthManager:
    def __init__(self, storage_dir: str = "storage/auth") -> None:
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def get_storage_path(self, platform: str) -> str:
        return str(self._dir / f"{platform}_state.json")

    async def save_state(self, ctx: BrowserContext, platform: str) -> None:
        path = self.get_storage_path(platform)
        await ctx.storage_state(path=str(path))
        logger.info("Saved auth state for %s", platform)

    async def load_state(self, ctx: BrowserContext, platform: str) -> bool:
        path = self.get_storage_path(platform)
        file = Path(path)
        if file.exists():
            await ctx.storage_state(path=path)
            logger.info("Loaded auth state for %s", platform)
            return True
        return False


class AutomationBrowser:
    def __init__(
        self,
        headless: bool = True,
        max_contexts: int = 5,
        downloads_dir: str = "downloads",
    ) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._headless = headless
        self._contexts = ContextPool(max_contexts)
        self._pages = PagePool()
        self._cookies = CookieManager()
        self._auth = AuthManager()
        self._downloads = Path(downloads_dir)
        self._downloads.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        if self._browser is not None:
            return
        self._playwright = await async_playwright().start()
        chromium: BrowserType = self._playwright.chromium
        self._browser = await chromium.launch(
            headless=self._headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        logger.info("Automation browser launched (headless=%s)", self._headless)

    async def new_context(
        self,
        *,
        platform: str = "",
        load_auth: bool = False,
        **kwargs: Any,
    ) -> BrowserContext:
        if self._browser is None:
            await self.start()
        assert self._browser is not None

        defaults: dict[str, Any] = {
            "viewport": {"width": 1280, "height": 900},
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
        }
        defaults.update(kwargs)

        ctx = await self._contexts.acquire(self._browser, **defaults)

        if platform and load_auth:
            await self._auth.load_state(ctx, platform)

        return ctx

    async def new_page(self, context: BrowserContext) -> Page:
        page = await self._pages.acquire(context)
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        return page

    async def release_page(self, page: Page) -> None:
        await self._pages.release(page)

    async def release_context(self, ctx: BrowserContext) -> None:
        await self._contexts.release(ctx)

    async def save_auth(self, ctx: BrowserContext, platform: str) -> None:
        await self._auth.save_state(ctx, platform)

    async def screenshot(self, page: Page, name: str) -> str:
        path = str(self._downloads / f"{name}.png")
        await page.screenshot(path=path, full_page=True)
        logger.debug("Screenshot saved: %s", path)
        return path

    async def download_path(self) -> str:
        return str(self._downloads)

    async def close(self) -> None:
        await self._pages.close_all()
        await self._contexts.close_all()
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Automation browser shut down")

    @property
    def is_running(self) -> bool:
        return self._browser is not None
