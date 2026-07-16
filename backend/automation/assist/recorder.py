"""Session Recorder — audit trail for automated applications.

Records every step, screenshot, error, validation result, and
submission outcome.  Provides full traceability for debugging
and compliance.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.automation.workflow.engine import StepResult

logger = logging.getLogger("job_hunting.automation.recorder")


@dataclass
class SessionStep:
    name: str
    status: str = "running"
    duration_ms: float = 0.0
    error: str | None = None
    screenshot: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class SessionRecord:
    session_id: str
    apply_url: str = ""
    platform: str = ""
    job_title: str = ""
    company: str = ""
    started_at: str = ""
    finished_at: str = ""
    steps: list[SessionStep] = field(default_factory=list)
    total_duration_ms: float = 0.0
    success: bool = False
    submission_verified: bool = False
    validation_result: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step_result: StepResult, screenshot: str | None = None) -> None:
        self.steps.append(
            SessionStep(
                name=step_result.name,
                status=step_result.status.value,
                duration_ms=round(step_result.duration_ms, 1),
                error=step_result.error,
                screenshot=screenshot,
                data=step_result.data,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )

    def set_submission(self, verified: bool) -> None:
        self.submission_verified = verified
        self.finished_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "apply_url": self.apply_url,
            "platform": self.platform,
            "job_title": self.job_title,
            "company": self.company,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "error": s.error,
                }
                for s in self.steps
            ],
            "total_duration_ms": self.total_duration_ms,
            "success": self.success,
            "submission_verified": self.submission_verified,
        }
