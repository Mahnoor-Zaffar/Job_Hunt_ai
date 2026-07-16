"""Form validation — pre-submission checks for required fields, formats, uploads."""

import logging
import re
from typing import Any

logger = logging.getLogger("job_hunting.automation.forms.validation")

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,15}$")


class FormValidator:
    async def validate_fields(
        self,
        fields: list[dict[str, Any]],
        required_field_names: list[str] | None = None,
    ) -> dict[str, Any]:
        issues: list[str] = []
        warnings: list[str] = []

        for field in fields:
            name = field.get("name", field.get("label", "unknown"))
            value = field.get("value", field.get("current_value", ""))

            if field.get("required") and not value:
                issues.append(f"Missing required field: {name}")

            if "email" in str(name).lower() and value and not EMAIL_RE.match(str(value)):
                issues.append(f"Invalid email format in: {name}")

            if (
                any(kw in str(name).lower() for kw in ["phone", "telephone", "mobile", "tel"])
                and value
                and not PHONE_RE.match(str(value))
            ):
                warnings.append(f"Possibly invalid phone number in: {name}")

            if field.get("type") == "file" and field.get("required") and not value:
                issues.append(f"File upload required: {name}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "total_fields": len(fields),
            "required_missing": len([i for i in issues if "Missing required" in i]),
        }

    @staticmethod
    def validate_input(field_name: str, value: str) -> dict[str, Any]:
        issues: list[str] = []
        if not value or not value.strip():
            issues.append(f"{field_name} is empty")
        if "email" in field_name.lower() and not EMAIL_RE.match(value):
            issues.append(f"{field_name} is not a valid email")
        return {"valid": len(issues) == 0, "issues": issues}
