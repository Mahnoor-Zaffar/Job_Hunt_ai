"""Intelligent Form Engine — detect, parse, and fill multi-step application forms."""

import logging
from typing import Any

from playwright.async_api import Page

from backend.automation.workflow.actions import (
    click,
    extract_form_fields,
    human_delay,
    wait_for_selector,
)

logger = logging.getLogger("job_hunting.automation.forms")

FIELD_TYPE_INDICATORS = {
    "text": ["text", "name", "email", "phone", "url", "city", "location"],
    "email": ["email", "e-mail"],
    "textarea": ["textarea", "description", "message", "cover", "why", "tell", "about"],
    "select": ["select", "dropdown", "choice"],
    "file": ["file", "upload", "resume", "cv", "attach"],
    "date": ["date", "calendar", "birthday", "available"],
    "checkbox": ["checkbox"],
    "radio": ["radio"],
}


class IntelligentFormEngine:
    def __init__(self, page: Page) -> None:
        self._page = page

    async def extract_all_fields(self) -> list[dict[str, Any]]:

        fields = await extract_form_fields(self._page)
        result: list[dict[str, Any]] = []
        for field in fields:
            result.append(
                {
                    "name": field.get("name", ""),
                    "tag": field.get("tag", ""),
                    "type": field.get("type", "text"),
                    "id": field.get("id", ""),
                    "label": field.get("label", ""),
                    "placeholder": field.get("placeholder", ""),
                    "required": self._is_required(field),
                    "selector": self._build_selector(field),
                    "detected_type": self._detect_field_type(field),
                }
            )
        return result

    async def detect_multi_step(self) -> bool:
        next_btn = await wait_for_selector(
            self._page,
            "button[type='submit'], .next-button, .continue-button, button.next, #next",
            timeout=3000,
        )
        prev_btn = await wait_for_selector(
            self._page,
            ".previous-button, .back-button, #previous, button.prev",
            timeout=3000,
        )
        return next_btn or prev_btn

    async def go_to_next_step(self) -> bool:
        for selector in [
            "button[type='submit']",
            ".next-button",
            ".continue-button",
            "button.next",
            "#next-step",
        ]:
            ok = await click(self._page, selector)
            if ok:
                await human_delay(500, 1000)
                return True
        return False

    async def fill_all_fields(self, data: dict[str, str]) -> int:
        from backend.automation.forms.mapper import FieldMapper
        from backend.automation.workflow.actions import fill_field

        mapper = FieldMapper()
        fields = await self.extract_all_fields()
        filled = 0

        for key, value in data.items():
            match = mapper.best_match(key, fields)
            if match:
                ok = await fill_field(self._page, match["selector"], value)
                if ok:
                    filled += 1
                    logger.debug("Filled %s → %s", key, match["selector"])
            else:
                logger.debug("No match for %s", key)

        return filled

    @staticmethod
    def _is_required(field: dict[str, Any]) -> bool:
        return bool(
            field.get("required")
            or "required" in str(field.get("attributes", ""))
            or "aria-required" in str(field.get("attributes", ""))
        )

    @staticmethod
    def _build_selector(field: dict[str, Any]) -> str:
        name = field.get("name", "")
        field_id = field.get("id", "")
        tag = field.get("tag", "input")
        if name:
            return f"{tag}[name='{name}']"
        if field_id:
            return f"#{field_id}"
        return str(tag)

    @staticmethod
    def _detect_field_type(field: dict[str, Any]) -> str:
        combined = (
            f"{field.get('name', '')} {field.get('label', '')} "
            f"{field.get('placeholder', '')} {field.get('id', '')} "
            f"{field.get('type', '')} {field.get('tag', '')}"
        ).lower()

        for ftype, keywords in FIELD_TYPE_INDICATORS.items():
            if any(kw in combined for kw in keywords):
                return ftype
        return "text"
