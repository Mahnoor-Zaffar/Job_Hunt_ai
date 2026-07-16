"""Workable adapter — apply.workable.com application forms."""

from typing import Any

from backend.automation.adapters.base import AdapterConfig, BaseATSAdapter
from backend.automation.adapters.detector import ATSPlatform


class WorkableAdapter(BaseATSAdapter):
    platform = ATSPlatform.WORKABLE

    def __init__(self, page: Any, apply_url: str) -> None:
        config = AdapterConfig(
            platform=ATSPlatform.WORKABLE,
            apply_url=apply_url,
            submit_selector="button[type='submit'], .workable-apply-submit",
            upload_resume_selector="input[type='file'][id*='resume'], #resume",
            confirm_selector=".application-success, .workable-thank-you",
            field_mapping={
                "first_name": ["firstname", "first_name", "given_name"],
                "last_name": ["lastname", "last_name", "family_name"],
                "email": ["email", "email_address"],
                "phone": ["phone", "phone_number"],
            },
        )
        super().__init__(page, config)

    async def detect_fields(self) -> list[dict[str, Any]]:
        from backend.automation.workflow.actions import extract_form_fields

        return await extract_form_fields(self._page)

    async def fill_form(self, data: dict[str, str]) -> int:
        from backend.automation.forms.mapper import FieldMapper
        from backend.automation.workflow.actions import fill_field

        mapper = FieldMapper()
        fields = await self.get_all_fields()
        filled = 0
        for key, value in data.items():
            match = mapper.best_match(key, fields)
            if match:
                ok = await fill_field(self._page, match["selector"], value)
                if ok:
                    filled += 1
        return filled
