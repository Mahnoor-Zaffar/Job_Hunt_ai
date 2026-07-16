"""Tests for ATS adapters and intelligent form engine."""

import pytest

from backend.automation.adapters.detector import (
    ATSPlatform,
    PlatformDetection,
    detect_from_url,
)
from backend.automation.forms.mapper import FIELD_ALIASES, FieldMapper
from backend.automation.forms.validation import FormValidator


class TestATSDetector:
    def test_detect_greenhouse_from_url(self) -> None:
        detection = detect_from_url("https://boards.greenhouse.io/motive/jobs/12345")
        assert detection.platform == ATSPlatform.GREENHOUSE
        assert detection.confidence >= 0.9

    def test_detect_lever_from_url(self) -> None:
        detection = detect_from_url("https://jobs.lever.co/arbisoft/abc123/apply")
        assert detection.platform == ATSPlatform.LEVER

    def test_detect_ashby_from_url(self) -> None:
        detection = detect_from_url("https://jobs.ashbyhq.com/testco/apply")
        assert detection.platform == ATSPlatform.ASHBY

    def test_detect_workable_from_url(self) -> None:
        detection = detect_from_url("https://apply.workable.com/systems/j/abc/apply")
        assert detection.platform == ATSPlatform.WORKABLE

    def test_unknown_url(self) -> None:
        detection = detect_from_url("https://www.example.com/jobs/apply")
        assert detection.platform == ATSPlatform.UNKNOWN
        assert detection.confidence == 0.0

    def test_detection_dataclass(self) -> None:
        d = PlatformDetection(platform=ATSPlatform.GREENHOUSE, confidence=0.9)
        assert d.platform == ATSPlatform.GREENHOUSE
        assert d.confidence == 0.9


class TestFieldMapper:
    def test_best_match_exact(self) -> None:
        mapper = FieldMapper()
        fields = [
            {"name": "first_name", "label": "First Name", "type": "text"},
            {"name": "email", "label": "Email Address", "type": "email"},
        ]
        match = mapper.best_match("first_name", fields)
        assert match is not None
        assert match["score"] >= 0.8

    def test_best_match_by_label(self) -> None:
        mapper = FieldMapper()
        fields = [
            {"name": "fn", "label": "First Name", "type": "text"},
        ]
        match = mapper.best_match("first_name", fields)
        assert match is not None
        assert match["score"] >= 0.7

    def test_best_match_email(self) -> None:
        mapper = FieldMapper()
        fields = [
            {"name": "email_address", "label": "Your Email", "type": "email"},
        ]
        match = mapper.best_match("email", fields)
        assert match is not None
        assert match["score"] >= 0.8

    def test_no_match(self) -> None:
        mapper = FieldMapper()
        fields = [
            {"name": "zzzzzzzz", "label": "Completely Unrelated", "type": "text"},
        ]
        match = mapper.best_match("first_name", fields)
        assert match is None

    def test_aliases_cover_all_keys(self) -> None:
        for key in ["first_name", "last_name", "email", "phone", "linkedin", "salary", "visa"]:
            assert key in FIELD_ALIASES


class TestFormValidator:
    @pytest.mark.asyncio
    async def test_valid_form(self) -> None:
        validator = FormValidator()
        fields = [
            {"name": "email", "label": "Email", "value": "test@example.com"},
            {"name": "name", "label": "Name", "value": "John"},
        ]
        result = await validator.validate_fields(fields)
        assert result["valid"] is True
        assert result["issues"] == []

    @pytest.mark.asyncio
    async def test_missing_required(self) -> None:
        validator = FormValidator()
        fields = [
            {"name": "email", "label": "Email", "required": True, "value": ""},
        ]
        result = await validator.validate_fields(fields)
        assert result["valid"] is False
        assert result["required_missing"] == 1

    @pytest.mark.asyncio
    async def test_invalid_email(self) -> None:
        validator = FormValidator()
        fields = [
            {"name": "email", "label": "Email", "value": "not-an-email"},
        ]
        result = await validator.validate_fields(fields)
        assert result["valid"] is False
        assert any("email" in i.lower() for i in result["issues"])

    @pytest.mark.asyncio
    async def test_missing_file(self) -> None:
        validator = FormValidator()
        fields = [
            {"name": "resume", "label": "Resume", "type": "file", "required": True, "value": ""},
        ]
        result = await validator.validate_fields(fields)
        assert result["valid"] is False

    def test_validate_input_email(self) -> None:
        assert FormValidator.validate_input("email", "test@example.com")["valid"] is True
        assert FormValidator.validate_input("email", "bad")["valid"] is False

    def test_validate_input_empty(self) -> None:
        assert FormValidator.validate_input("name", "")["valid"] is False
        assert FormValidator.validate_input("name", "John")["valid"] is True


class TestATSPlatformEnum:
    def test_values(self) -> None:
        platforms = {
            ATSPlatform.GREENHOUSE,
            ATSPlatform.LEVER,
            ATSPlatform.ASHBY,
            ATSPlatform.WORKABLE,
        }
        assert ATSPlatform.UNKNOWN not in platforms
