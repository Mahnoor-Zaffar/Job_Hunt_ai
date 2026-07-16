"""Greenhouse adapter — boards.greenhouse.io application forms."""

from typing import Any

from backend.automation.adapters.base import AdapterConfig, BaseATSAdapter
from backend.automation.adapters.detector import ATSPlatform


class GreenhouseAdapter(BaseATSAdapter):
    platform = ATSPlatform.GREENHOUSE

    def __init__(self, page: Any, apply_url: str) -> None:
        config = AdapterConfig(
            platform=ATSPlatform.GREENHOUSE,
            apply_url=apply_url,
            submit_selector="input#submit_app, button#submit_app, .button--primary",
            upload_resume_selector="input[type='file'][id*='resume'], input[type='file'][name*='resume']",
            upload_cover_selector="input[type='file'][id*='cover'], input[type='file'][name*='cover']",
            confirm_selector=".application-complete, .thank-you, #application_confirmation",
            field_mapping={
                "first_name": ["first_name", "firstname", "given_name"],
                "last_name": ["last_name", "lastname", "family_name"],
                "email": ["email", "email_address"],
                "phone": ["phone", "phone_number", "telephone"],
                "resume": ["resume", "resume_upload", "resume_file"],
                "cover_letter": ["cover_letter", "cover_letter_file"],
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
