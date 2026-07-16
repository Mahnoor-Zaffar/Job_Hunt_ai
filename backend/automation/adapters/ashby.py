"""Ashby adapter — jobs.ashbyhq.com application forms."""

from typing import Any

from backend.automation.adapters.base import AdapterConfig, BaseATSAdapter
from backend.automation.adapters.detector import ATSPlatform


class AshbyAdapter(BaseATSAdapter):
    platform = ATSPlatform.ASHBY

    def __init__(self, page: Any, apply_url: str) -> None:
        config = AdapterConfig(
            platform=ATSPlatform.ASHBY,
            apply_url=apply_url,
            submit_selector="button[type='submit'], .ashby-application-submit",
            upload_resume_selector="input[type='file']",
            confirm_selector=".ashby-thank-you, .application-success",
            field_mapping={
                "first_name": ["first_name", "firstName", "given_name"],
                "last_name": ["last_name", "lastName", "family_name"],
                "email": ["email", "emailAddress"],
                "phone": ["phone", "phoneNumber"],
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
