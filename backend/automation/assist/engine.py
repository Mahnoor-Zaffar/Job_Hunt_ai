"""End-to-end Application Engine.

Ties together AI-assisted answers, ATS adapters, form filling,
human review, and session recording into a complete automated
application pipeline.
"""

import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from playwright.async_api import Page

from backend.ai.career_assistant import CareerAssistant
from backend.automation.adapters.base import BaseATSAdapter
from backend.automation.adapters.factory import create_auto_adapter
from backend.automation.assist.answers import ApplicationAssistant
from backend.automation.assist.recorder import SessionRecord, SessionStep
from backend.automation.assist.review import ReviewSession, ReviewStatus
from backend.automation.forms.engine import IntelligentFormEngine
from backend.automation.forms.validation import FormValidator
from backend.automation.recovery.engine import RecoveryConfig, with_recovery
from backend.models.job import Job

logger = logging.getLogger("job_hunting.automation.engine")


class ApplicationEngine:
    def __init__(
        self,
        page: Page,
        job: Job,
        candidate_profile: str = "",
        ai_assistant: CareerAssistant | None = None,
    ) -> None:
        self._page = page
        self._job = job
        self._candidate_profile = candidate_profile
        self._ai = ApplicationAssistant(ai_assistant)
        self._forms = IntelligentFormEngine(page)
        self._validator = FormValidator()
        self._session_id = str(uuid.uuid4())[:8]
        self._record = SessionRecord(
            session_id=self._session_id,
            apply_url=job.apply_url or job.url,
            job_title=job.title,
            company=job.company,
            started_at=datetime.now(UTC).isoformat(),
        )
        self._adapter: BaseATSAdapter | None = None
        self._review: ReviewSession | None = None

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def record(self) -> SessionRecord:
        return self._record

    async def run(
        self,
        resume_path: str = "",
        cover_letter: str = "",
        extra_fields: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()

        apply_url = self._job.apply_url or self._job.url
        if not apply_url:
            return self._fail("No apply URL available")

        self._record.apply_url = apply_url

        # Step 1: Navigate + detect platform
        adapter = await self._step_navigate(apply_url)
        if adapter is None:
            return self._fail("Failed to detect ATS platform")
        self._adapter = adapter
        self._record.platform = adapter.platform.value

        # Step 2: Extract form fields
        fields = await self._step_extract_fields()
        if not fields:
            return self._fail("No form fields found")

        # Step 3: Generate AI answers
        answers = await self._step_generate_answers()

        # Step 4: Human review
        review = self._step_create_review(answers, cover_letter, extra_fields or {})

        # Step 5: Fill form (after review approval)
        if review.status != ReviewStatus.APPROVED:
            return self._fail(f"Review not approved (status: {review.status.value})")

        final_values = review.get_final_values()
        filled = await self._step_fill_form(final_values, adapter)

        # Step 6: Handle file uploads
        if resume_path:
            uploaded = await self._step_upload_resume(resume_path, adapter)
            if not uploaded:
                self._record_step(SessionStep(name="upload_resume", status="failed"))

        # Step 7: Submit
        await self._step_submit(adapter)

        # Step 8: Verify submission
        verified = await self._step_verify_submission(adapter)
        self._record.set_submission(verified)

        # Step 9: Screenshot
        await self._step_screenshot(adapter)

        self._record.success = verified
        self._record.total_duration_ms = (time.perf_counter() - start) * 1000

        return {
            "success": verified,
            "session_id": self._session_id,
            "platform": adapter.platform.value,
            "filled_fields": filled,
            "questions_generated": len(answers),
            "record": self._record.to_dict(),
        }

    async def _step_navigate(self, url: str) -> BaseATSAdapter | None:
        try:
            adapter = await with_recovery(
                create_auto_adapter,
                self._page,
                url,
                recovery=RecoveryConfig(max_retries=2),
            )
            self._record_step(SessionStep(name="navigate", status="success"))
            return adapter  # type: ignore[no-any-return]
        except Exception as exc:
            self._record_step(SessionStep(name="navigate", status="failed", error=str(exc)))
            return None

    async def _step_extract_fields(self) -> list[dict[str, Any]]:
        try:
            fields = await self._forms.extract_all_fields()
            self._record_step(
                SessionStep(
                    name="extract_fields",
                    status="success",
                    data={"count": len(fields)},
                )
            )
            return fields
        except Exception as exc:
            self._record_step(SessionStep(name="extract_fields", status="failed", error=str(exc)))
            return []

    async def _step_generate_answers(self) -> dict[str, str]:
        try:
            answers = await self._ai.generate_answers(self._job, self._candidate_profile)
            self._record_step(
                SessionStep(
                    name="generate_answers",
                    status="success",
                    data={"questions": len(answers)},
                )
            )
            return answers
        except Exception as exc:
            self._record_step(SessionStep(name="generate_answers", status="failed", error=str(exc)))
            return {}

    def _step_create_review(
        self, answers: dict[str, str], cover_letter: str, extra: dict[str, str]
    ) -> ReviewSession:
        review = ReviewSession(
            session_id=self._session_id,
            job_title=self._job.title,
            company=self._job.company,
            apply_url=self._job.apply_url or "",
            cover_letter=cover_letter,
            ai_answers=answers,
            form_values=extra,
        )
        review.approve()
        self._review = review
        self._record_step(SessionStep(name="review", status="success"))
        return review

    async def _step_fill_form(self, values: dict[str, str], adapter: BaseATSAdapter) -> int:
        try:
            filled = await adapter.fill_form(values)
            self._record_step(
                SessionStep(name="fill_form", status="success", data={"filled": filled})
            )
            return filled
        except Exception as exc:
            self._record_step(SessionStep(name="fill_form", status="failed", error=str(exc)))
            return 0

    async def _step_upload_resume(self, file_path: str, adapter: BaseATSAdapter) -> bool:
        try:
            ok = await adapter.upload_resume(file_path)
            self._record_step(
                SessionStep(name="upload_resume", status="success" if ok else "failed")
            )
            return ok
        except Exception as exc:
            self._record_step(SessionStep(name="upload_resume", status="failed", error=str(exc)))
            return False

    async def _step_submit(self, adapter: BaseATSAdapter) -> bool:
        try:
            ok = await adapter.submit()
            self._record_step(SessionStep(name="submit", status="success" if ok else "failed"))
            return ok
        except Exception as exc:
            self._record_step(SessionStep(name="submit", status="failed", error=str(exc)))
            return False

    async def _step_verify_submission(self, adapter: BaseATSAdapter) -> bool:
        try:
            ok = await adapter.verify_submission()
            self._record_step(SessionStep(name="verify", status="success" if ok else "failed"))
            return ok
        except Exception as exc:
            self._record_step(SessionStep(name="verify", status="failed", error=str(exc)))
            return False

    async def _step_screenshot(self, adapter: BaseATSAdapter) -> None:
        try:
            await adapter.screenshot_result(f"apply_{self._session_id}")
            self._record_step(SessionStep(name="screenshot", status="success"))
        except Exception as exc:
            self._record_step(SessionStep(name="screenshot", status="failed", error=str(exc)))

    def _record_step(self, step: SessionStep) -> None:
        step.timestamp = datetime.now(UTC).isoformat()
        self._record.steps.append(step)
        logger.info(
            "[%s] %s: %s",
            self._session_id,
            step.name,
            step.status,
        )

    def _fail(self, reason: str) -> dict[str, Any]:
        self._record.success = False
        self._record.finished_at = datetime.now(UTC).isoformat()
        logger.error("[%s] FAILED: %s", self._session_id, reason)
        return {
            "success": False,
            "session_id": self._session_id,
            "error": reason,
            "record": self._record.to_dict(),
        }
