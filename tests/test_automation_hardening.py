"""Production readiness tests for automation platform — security, reliability, observability."""

from unittest.mock import MagicMock

import pytest

from backend.automation.observability import AutomationMetrics, get_metrics
from backend.automation.reliability import AutomationTimeout, force_garbage_collection
from backend.automation.security import (
    check_credentials,
    sanitize_form_data,
    sanitize_log,
    validate_apply_url,
    validate_upload_path,
)


class TestSecurity:
    def test_sanitize_log_removes_email(self) -> None:
        result = sanitize_log("Contact: john@example.com for details")
        assert "john@example.com" not in result
        assert "[EMAIL_REDACTED]" in result

    def test_sanitize_log_removes_phone(self) -> None:
        result = sanitize_log("Call +1-555-0123 for info")
        assert "+1-555-0123" not in result
        assert "[PHONE_REDACTED]" in result

    def test_sanitize_log_removes_password(self) -> None:
        result = sanitize_log("password=myp@ssw0rd token=abc123")
        assert "myp@ssw0rd" not in result
        assert "abc123" not in result

    def test_sanitize_log_truncates_long_content(self) -> None:
        long_text = "A" * 2000
        result = sanitize_log(long_text)
        assert len(result) <= 500

    def test_sanitize_form_data(self) -> None:
        data = {"email": "john@test.com", "name": "John", "phone": "+1-555-0123"}
        result = sanitize_form_data(data)
        assert result["name"] == "John"
        assert "john@test.com" not in result["email"]
        assert "+1-555-0123" not in result["phone"]

    def test_validate_apply_url_https(self) -> None:
        assert validate_apply_url("https://boards.greenhouse.io/apply") is True

    def test_validate_apply_url_invalid(self) -> None:
        assert validate_apply_url("ftp://evil.com") is False
        assert validate_apply_url("not-a-url") is False

    def test_check_credentials(self) -> None:
        result = check_credentials()
        assert "openrouter_key_set" in result
        assert "telegram_token_set" in result

    def test_validate_upload_path_not_found(self) -> None:
        assert validate_upload_path("/nonexistent/file.pdf") is False


class TestReliability:
    def test_timeout_defaults(self) -> None:
        timeout = AutomationTimeout()
        assert timeout.get("navigation") == 30
        assert timeout.get("click") == 10
        assert timeout.get("unknown", default=5) == 5

    def test_timeout_override(self) -> None:
        timeout = AutomationTimeout()
        timeout.override("navigation", 60)
        assert timeout.get("navigation") == 60

    @pytest.mark.asyncio
    async def test_force_garbage_collection(self) -> None:
        await force_garbage_collection()


class TestObservability:
    def test_metrics_record_workflow(self) -> None:
        metrics = AutomationMetrics()
        metrics.record_workflow(success=True, duration_ms=1000)
        metrics.record_workflow(success=False, duration_ms=500)
        snap = metrics.snapshot()
        assert snap["workflows"]["total"] == 2
        assert snap["workflows"]["succeeded"] == 1
        assert snap["workflows"]["success_rate"] == 0.5

    def test_metrics_record_step(self) -> None:
        metrics = AutomationMetrics()
        metrics.record_step("navigate", True)
        metrics.record_step("fill_form", False)
        metrics.record_step("upload_resume", False)
        metrics.record_step("submit", False)
        snap = metrics.snapshot()
        assert snap["steps"]["total"] == 4
        assert snap["steps"]["failed"] == 3
        assert snap["failures"]["navigation"] == 0
        assert snap["failures"]["form_fill"] == 1
        assert snap["failures"]["upload"] == 1
        assert snap["failures"]["submission"] == 1

    def test_metrics_snapshot_structure(self) -> None:
        metrics = AutomationMetrics()
        snap = metrics.snapshot()
        assert "workflows" in snap
        assert "steps" in snap
        assert "failures" in snap
        assert "avg_duration_ms" in snap

    def test_global_metrics_singleton(self) -> None:
        m1 = get_metrics()
        m2 = get_metrics()
        assert m1 is m2


class TestAdapterFailureRecovery:
    def test_factory_unknown_url(self) -> None:
        from backend.automation.adapters.factory import create_adapter

        adapter = create_adapter(MagicMock(), "https://example.com/jobs")
        assert adapter is None

    def test_detector_confidence_scores(self) -> None:
        from backend.automation.adapters.detector import (
            ATSPlatform,
            detect_from_url,
        )

        d = detect_from_url("https://boards.greenhouse.io/motive/jobs/123")
        assert d.confidence >= 0.9
        assert d.platform == ATSPlatform.GREENHOUSE

        d2 = detect_from_url("https://random.com/apply")
        assert d2.confidence == 0.0
        assert d2.platform == ATSPlatform.UNKNOWN
