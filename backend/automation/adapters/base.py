"""Base ATS adapter — defines the interface all platform adapters implement."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import Page

from backend.automation.adapters.detector import ATSPlatform
from backend.automation.forms.engine import IntelligentFormEngine
from backend.automation.forms.validation import FormValidator

logger = logging.getLogger("job_hunting.automation.adapters")


@dataclass
class AdapterConfig:
    platform: ATSPlatform
    apply_url: str
    submit_selector: str = "button[type='submit'], input[type='submit'], .submit-button"
    upload_resume_selector: str = "input[type='file']"
    upload_cover_selector: str = "input[type='file'][name*='cover']"
    confirm_selector: str = ".confirmation, .success-message"
    field_mapping: dict[str, list[str]] = field(default_factory=dict)
    extra_selectors: dict[str, str] = field(default_factory=dict)


class BaseATSAdapter(ABC):
    platform: ATSPlatform = ATSPlatform.UNKNOWN

    def __init__(self, page: Page, config: AdapterConfig) -> None:
        self._page = page
        self._config = config
        self._forms = IntelligentFormEngine(page)
        self._validator = FormValidator()

    @abstractmethod
    async def detect_fields(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def fill_form(self, data: dict[str, str]) -> int: ...

    async def navigate(self) -> bool:
        from backend.automation.workflow.actions import navigate

        return await navigate(self._page, self._config.apply_url)

    async def upload_resume(self, file_path: str) -> bool:
        from backend.automation.workflow.actions import upload_file

        return await upload_file(self._page, self._config.upload_resume_selector, file_path)

    async def upload_cover_letter(self, file_path: str) -> bool:
        from backend.automation.workflow.actions import upload_file

        return await upload_file(self._page, self._config.upload_cover_selector, file_path)

    async def submit(self) -> bool:
        from backend.automation.workflow.actions import click

        return await click(self._page, self._config.submit_selector)

    async def verify_submission(self) -> bool:
        from backend.automation.workflow.actions import wait_for_selector

        return await wait_for_selector(self._page, self._config.confirm_selector, timeout=8000)

    async def screenshot_result(self, name: str = "application") -> str:
        path = f"screenshots/{name}_{self.platform.value}.png"
        await self._page.screenshot(path=path, full_page=True)
        return path

    async def get_all_fields(self) -> list[dict[str, Any]]:
        return await self._forms.extract_all_fields()

    async def validate_form(self, required_fields: list[str] | None = None) -> dict[str, Any]:
        fields = await self.get_all_fields()
        return await self._validator.validate_fields(fields, required_fields)
