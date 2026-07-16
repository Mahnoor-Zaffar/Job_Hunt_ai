"""Action executor — reusable Playwright interactions.

Every action is a standalone async function that operates on a
Playwright Page.  Actions handle their own timeouts, retries, and
error logging.  Used by the workflow engine to compose automation
pipelines.
"""

import asyncio
import logging

from playwright.async_api import Page

logger = logging.getLogger("job_hunting.automation.actions")


async def navigate(page: Page, url: str, *, timeout: int = 30000) -> bool:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        logger.debug("Navigated to %s", url[:60])
        return True
    except Exception as exc:
        logger.error("Navigation failed: %s — %s", url[:60], exc)
        return False


async def wait_for_selector(
    page: Page, selector: str, *, timeout: int = 10000, state: str = "visible"
) -> bool:
    try:
        await page.wait_for_selector(selector, timeout=timeout, state=state)  # type: ignore[arg-type]
        return True
    except Exception:
        logger.debug("Selector not found: %s", selector)
        return False


async def click(page: Page, selector: str, *, timeout: int = 5000) -> bool:
    try:
        await page.click(selector, timeout=timeout)
        return True
    except Exception as exc:
        logger.debug("Click failed: %s — %s", selector, exc)
        return False


async def type_text(
    page: Page, selector: str, text: str, *, clear: bool = True, delay: int = 50
) -> bool:
    try:
        if clear:
            await page.fill(selector, "")
        await page.type(selector, text, delay=delay)
        return True
    except Exception as exc:
        logger.debug("Type failed: %s — %s", selector, exc)
        return False


async def fill_field(page: Page, selector: str, value: str) -> bool:
    try:
        await page.fill(selector, value)
        return True
    except Exception as exc:
        logger.debug("Fill failed: %s — %s", selector, exc)
        return False


async def select_option(
    page: Page, selector: str, value: str | None = None, label: str | None = None
) -> bool:
    try:
        if value:
            await page.select_option(selector, value=value)
        elif label:
            await page.select_option(selector, label=label)
        return True
    except Exception as exc:
        logger.debug("Select failed: %s — %s", selector, exc)
        return False


async def upload_file(page: Page, selector: str, file_path: str) -> bool:
    try:
        await page.set_input_files(selector, file_path)
        return True
    except Exception as exc:
        logger.debug("Upload failed: %s — %s", selector, exc)
        return False


async def extract_text(page: Page, selector: str) -> str | None:
    try:
        element = await page.query_selector(selector)
        if element:
            return await element.text_content()
        return None
    except Exception:
        return None


async def extract_form_fields(page: Page) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    try:
        inputs = await page.query_selector_all("input, textarea, select")
        for el in inputs:
            name = await el.get_attribute("name") or ""
            tag = await el.evaluate("el => el.tagName.toLowerCase()")
            el_type = await el.get_attribute("type") or "text"
            placeholder = await el.get_attribute("placeholder") or ""
            label_text = ""
            try:
                label = await el.evaluate(
                    """el => {
                    const lbl = el.closest('label');
                    return lbl ? lbl.textContent?.trim() : '';
                }"""
                )
                label_text = str(label).strip() if label else ""
            except Exception:
                pass
            fields.append(
                {
                    "name": name,
                    "tag": str(tag),
                    "type": str(el_type),
                    "placeholder": str(placeholder),
                    "label": str(label_text),
                }
            )
    except Exception:
        pass
    return fields


async def wait_for_navigation(page: Page, *, timeout: int = 15000) -> bool:
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
        return True
    except Exception:
        return False


async def scroll_into_view(page: Page, selector: str) -> bool:
    try:
        await page.locator(selector).scroll_into_view_if_needed()
        return True
    except Exception:
        return False


async def human_delay(min_ms: int = 200, max_ms: int = 800) -> None:
    import random

    await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)
