"""ATS adapter factory — auto-detects platform and returns the right adapter."""

from playwright.async_api import Page

from backend.automation.adapters.ashby import AshbyAdapter
from backend.automation.adapters.base import BaseATSAdapter
from backend.automation.adapters.detector import ATSPlatform, detect_from_url
from backend.automation.adapters.greenhouse import GreenhouseAdapter
from backend.automation.adapters.lever import LeverAdapter
from backend.automation.adapters.workable import WorkableAdapter

ADAPTER_MAP: dict[ATSPlatform, type[BaseATSAdapter]] = {
    ATSPlatform.GREENHOUSE: GreenhouseAdapter,
    ATSPlatform.LEVER: LeverAdapter,
    ATSPlatform.ASHBY: AshbyAdapter,
    ATSPlatform.WORKABLE: WorkableAdapter,
}


def create_adapter(page: Page, apply_url: str) -> BaseATSAdapter | None:
    detection = detect_from_url(apply_url)
    if detection.platform == ATSPlatform.UNKNOWN:
        return None

    adapter_cls = ADAPTER_MAP.get(detection.platform)
    if adapter_cls is None:
        return None

    return adapter_cls(page, apply_url)  # type: ignore[arg-type]


async def create_auto_adapter(page: Page, url: str) -> BaseATSAdapter | None:
    from backend.automation.workflow.actions import navigate

    detection = detect_from_url(url)
    if detection.platform == ATSPlatform.UNKNOWN:
        ok = await navigate(page, url)
        if not ok:
            return None
        content = await page.content()
        title = await page.title()
        from backend.automation.adapters.detector import detect_from_page

        detection = detect_from_page(url, content, title)
        if detection.platform == ATSPlatform.UNKNOWN:
            return None

    adapter_cls = ADAPTER_MAP.get(detection.platform)
    if adapter_cls is None:
        return None

    return adapter_cls(page, url)  # type: ignore[arg-type]
