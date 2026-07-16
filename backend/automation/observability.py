"""Observability hooks for the automation platform.

Tracks automation metrics, provides health checks, and formats
structured logs for Prometheus/Grafana integration.
"""

import logging
from typing import Any

logger = logging.getLogger("job_hunting.automation.observability")


class AutomationMetrics:
    def __init__(self) -> None:
        self._workflows_total = 0
        self._workflows_succeeded = 0
        self._workflows_failed = 0
        self._steps_total = 0
        self._steps_failed = 0
        self._total_duration_ms = 0.0
        self._navigation_failures = 0
        self._form_fill_failures = 0
        self._upload_failures = 0
        self._submission_failures = 0

    def record_workflow(self, success: bool, duration_ms: float) -> None:
        self._workflows_total += 1
        self._total_duration_ms += duration_ms
        if success:
            self._workflows_succeeded += 1
        else:
            self._workflows_failed += 1

    def record_step(self, name: str, success: bool) -> None:
        self._steps_total += 1
        if not success:
            self._steps_failed += 1
            if "navigat" in name.lower():
                self._navigation_failures += 1
            elif "fill" in name.lower():
                self._form_fill_failures += 1
            elif "upload" in name.lower():
                self._upload_failures += 1
            elif "submit" in name.lower():
                self._submission_failures += 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "workflows": {
                "total": self._workflows_total,
                "succeeded": self._workflows_succeeded,
                "failed": self._workflows_failed,
                "success_rate": round(self._workflows_succeeded / max(1, self._workflows_total), 2),
            },
            "steps": {
                "total": self._steps_total,
                "failed": self._steps_failed,
            },
            "failures": {
                "navigation": self._navigation_failures,
                "form_fill": self._form_fill_failures,
                "upload": self._upload_failures,
                "submission": self._submission_failures,
            },
            "avg_duration_ms": round(self._total_duration_ms / max(1, self._workflows_total), 1),
        }


_global_metrics = AutomationMetrics()


def get_metrics() -> AutomationMetrics:
    return _global_metrics


async def automation_health_check() -> dict[str, Any]:
    try:
        from backend.automation.browser.manager import AutomationBrowser

        browser = AutomationBrowser(headless=True)
        await browser.start()
        is_running = browser.is_running
        await browser.close()

        return {
            "status": "healthy" if is_running else "degraded",
            "browser": "ok" if is_running else "failed",
            "playwright_available": True,
            "metrics": _global_metrics.snapshot(),
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "browser": "error",
            "error": str(exc),
            "playwright_available": False,
        }
