"""Automated job application workflow.

A reusable workflow that automates the job application process:
navigate → detect form → fill fields → upload resume → confirm → submit.

Can be configured per ATS platform via field mappings.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.automation.workflow.engine import (
    WorkflowEngine,
    WorkflowResult,
    step_click,
    step_fill,
    step_navigate,
    step_screenshot,
    step_upload,
    step_wait,
)

logger = logging.getLogger("job_hunting.automation.apply")


@dataclass
class ApplicationConfig:
    apply_url: str
    field_mapping: dict[str, str] = field(default_factory=dict)
    submit_selector: str = "button[type='submit'], input[type='submit'], .submit-button"
    confirm_required: bool = True
    confirm_selector: str = ".confirmation, .success-message"
    upload_resume_selector: str = "input[type='file']"
    resume_path: str = ""


class AutoApplyWorkflow:
    def __init__(self, page: Any, config: ApplicationConfig) -> None:
        self._page = page
        self._config = config
        self._engine = WorkflowEngine(page, name="auto-apply")

    async def run(self, field_values: dict[str, str]) -> WorkflowResult:
        steps: list[Any] = [
            ("navigate", step_navigate, {"url": self._config.apply_url}),
            (
                "wait_for_form",
                step_wait,
                {"selector": "form, input, .application-form", "timeout": 15000},
            ),
        ]

        for field_name, selector in self._config.field_mapping.items():
            if field_name in field_values:
                steps.append(
                    (
                        f"fill_{field_name}",
                        step_fill,
                        {"selector": selector, "value": field_values[field_name]},
                    )
                )

        if self._config.resume_path and self._config.upload_resume_selector:
            steps.append(
                (
                    "upload_resume",
                    step_upload,
                    {
                        "selector": self._config.upload_resume_selector,
                        "file_path": self._config.resume_path,
                    },
                )
            )

        steps.append(("submit", step_click, {"selector": self._config.submit_selector}))

        if self._config.confirm_required:
            steps.append(
                (
                    "confirm",
                    step_wait,
                    {"selector": self._config.confirm_selector, "timeout": 10000},
                )
            )

        steps.append(("screenshot", step_screenshot, {"name": "apply_result"}))

        result = await self._engine.run(steps, **field_values)
        return result
