"""Human Review Mode — structured review before submission.

Captures all application data (resume, cover letter, AI answers, form
values) and presents them for human review.  Submission requires
explicit confirmation.  Designed to be consumed by a UI layer.
"""

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("job_hunting.automation.review")


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


@dataclass
class ReviewSession:
    session_id: str
    job_title: str = ""
    company: str = ""
    apply_url: str = ""
    resume_text: str = ""
    cover_letter: str = ""
    ai_answers: dict[str, str] = field(default_factory=dict)
    form_values: dict[str, str] = field(default_factory=dict)
    edited_values: dict[str, str] = field(default_factory=dict)
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer_notes: str = ""
    submitted_at: str = ""

    def approve(self) -> None:
        self.status = ReviewStatus.APPROVED

    def reject(self, reason: str = "") -> None:
        self.status = ReviewStatus.REJECTED
        self.reviewer_notes = reason

    def edit(self, field: str, value: str) -> None:
        self.edited_values[field] = value
        self.status = ReviewStatus.EDITED

    def get_final_values(self) -> dict[str, str]:
        final = {**self.ai_answers, **self.form_values, **self.edited_values}
        return final

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "job_title": self.job_title,
            "company": self.company,
            "apply_url": self.apply_url,
            "ai_answers": self.ai_answers,
            "form_values": self.form_values,
            "edited_values": self.edited_values,
            "status": self.status.value,
            "reviewer_notes": self.reviewer_notes,
        }
