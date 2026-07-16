"""Tests for the AI-assisted application engine."""

from unittest.mock import AsyncMock

import pytest

from backend.automation.assist.answers import ApplicationAssistant, STANDARD_QUESTIONS
from backend.automation.assist.recorder import SessionRecord, SessionStep
from backend.automation.assist.review import ReviewSession, ReviewStatus
from backend.models.job import Job


class TestApplicationAssistant:
    @pytest.fixture
    def mock_ai(self) -> AsyncMock:
        ai = AsyncMock()
        ai._ai = AsyncMock()
        ai._ai.generate_text = AsyncMock(
            return_value="This is a generated answer for the application."
        )
        return ai

    @pytest.mark.asyncio
    async def test_generate_answers(self, mock_ai: AsyncMock) -> None:
        job = Job(
            title="Software Engineer", company="Acme Corp",
            location="Islamabad", url="https://example.com/job",
            source="test", source_id="1", fingerprint="abc",
            description="Build APIs with Python and FastAPI.",
        )
        assistant = ApplicationAssistant(ai=mock_ai)
        answers = await assistant.generate_answers(
            job, "Backend engineer with 5 years experience."
        )
        assert isinstance(answers, dict)
        for q in STANDARD_QUESTIONS:
            assert q in answers

    @pytest.mark.asyncio
    async def test_specific_questions(self, mock_ai: AsyncMock) -> None:
        job = Job(
            title="Engineer", company="Co", location="Remote",
            url="https://x.com", source="t", source_id="si", fingerprint="f",
        )
        assistant = ApplicationAssistant(ai=mock_ai)
        answers = await assistant.generate_answers(
            job, "Experienced developer.",
            questions=["motivation", "salary_expectations"],
        )
        assert "motivation" in answers
        assert "salary_expectations" in answers

    @pytest.mark.asyncio
    async def test_ai_failure_returns_empty(self, mock_ai: AsyncMock) -> None:
        job = Job(
            title="Engineer", company="Co", location="Remote",
            url="https://x.com", source="t", source_id="si", fingerprint="f",
        )
        mock_ai._ai.generate_text = AsyncMock(side_effect=RuntimeError("OpenRouter down"))
        assistant = ApplicationAssistant(ai=mock_ai)
        answers = await assistant.generate_answers(
            job, "", questions=["motivation"]
        )
        assert answers["motivation"] == ""


class TestReviewSession:
    def test_approve(self) -> None:
        session = ReviewSession(session_id="abc", job_title="Dev", company="Acme")
        assert session.status == ReviewStatus.PENDING
        session.approve()
        assert session.status == ReviewStatus.APPROVED

    def test_reject(self) -> None:
        session = ReviewSession(session_id="abc")
        session.reject("Wrong job")
        assert session.status == ReviewStatus.REJECTED
        assert session.reviewer_notes == "Wrong job"

    def test_edit(self) -> None:
        session = ReviewSession(session_id="abc", ai_answers={"motivation": "old"})
        session.edit("motivation", "new answer")
        assert session.status == ReviewStatus.EDITED
        assert session.edited_values["motivation"] == "new answer"

    def test_get_final_values(self) -> None:
        session = ReviewSession(
            session_id="abc",
            ai_answers={"motivation": "AI answer", "salary": "100k"},
            form_values={"name": "John"},
            edited_values={"motivation": "Edited answer"},
        )
        final = session.get_final_values()
        assert final["name"] == "John"
        assert final["motivation"] == "Edited answer"
        assert final["salary"] == "100k"

    def test_to_dict(self) -> None:
        session = ReviewSession(
            session_id="xyz", job_title="Engineer", company="Acme",
            apply_url="https://apply.example.com",
        )
        d = session.to_dict()
        assert d["session_id"] == "xyz"
        assert d["status"] == "pending"


class TestSessionRecord:
    def test_add_step(self) -> None:
        from backend.automation.workflow.engine import StepResult, StepStatus

        record = SessionRecord(session_id="test", apply_url="https://x.com")
        step = StepResult(name="navigate", status=StepStatus.SUCCESS)
        record.add_step(step)
        assert len(record.steps) == 1
        assert record.steps[0].name == "navigate"

    def test_set_submission(self) -> None:
        record = SessionRecord(session_id="test")
        record.set_submission(True)
        assert record.submission_verified is True
        assert record.finished_at != ""

    def test_to_dict(self) -> None:
        record = SessionRecord(
            session_id="test", apply_url="https://x.com",
            platform="greenhouse", job_title="Engineer",
            company="Acme", success=True,
        )
        d = record.to_dict()
        assert d["session_id"] == "test"
        assert d["platform"] == "greenhouse"
        assert d["success"] is True


class TestSessionStep:
    def test_defaults(self) -> None:
        step = SessionStep(name="test")
        assert step.name == "test"
        assert step.status == "running"
        assert step.error is None
