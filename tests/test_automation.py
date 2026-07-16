"""Tests for the automation platform — workflow engine, recovery, configs."""

from unittest.mock import AsyncMock

import pytest

from backend.automation.recovery.engine import RecoveryConfig, with_recovery
from backend.automation.workflow.apply import ApplicationConfig, AutoApplyWorkflow
from backend.automation.workflow.engine import StepResult, StepStatus, WorkflowEngine


class TestRecoveryEngine:
    @pytest.mark.asyncio
    async def test_succeeds_first_try(self) -> None:
        call_count = 0

        async def succeed() -> str:
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await with_recovery(succeed, recovery=RecoveryConfig(max_retries=3))
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_then_succeeds(self) -> None:
        call_count = 0

        async def flaky() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("fail")
            return "ok"

        result = await with_recovery(
            flaky, recovery=RecoveryConfig(max_retries=3, base_delay_seconds=0.01)
        )
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries(self) -> None:
        async def always_fail() -> str:
            raise RuntimeError("always")

        with pytest.raises(RuntimeError, match="always"):
            await with_recovery(
                always_fail, recovery=RecoveryConfig(max_retries=2, base_delay_seconds=0.01)
            )

    @pytest.mark.asyncio
    async def test_on_retry_callback(self) -> None:
        retries_recorded: list[int] = []

        async def fail() -> None:
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await with_recovery(
                fail,
                recovery=RecoveryConfig(max_retries=2, base_delay_seconds=0.01),
                on_retry=lambda n, _: retries_recorded.append(n),
            )
        assert retries_recorded == [1, 2]


class TestWorkflowEngine:
    @pytest.mark.asyncio
    async def test_runs_all_steps(self) -> None:
        page = AsyncMock()
        engine = WorkflowEngine(page, name="test")

        async def step_a(page, context):
            return {"a": 1}

        async def step_b(page, context):
            return {"b": 2}

        result = await engine.run([("a", step_a, {}), ("b", step_b, {})])
        assert result.success is True
        assert len(result.steps) == 2
        assert result.steps[0].status == StepStatus.SUCCESS
        assert result.steps[1].status == StepStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_stops_on_failure(self) -> None:
        page = AsyncMock()
        engine = WorkflowEngine(page, name="test")

        async def step_a(page, context):
            return {"ok": True}

        async def step_fail(page, context):
            raise RuntimeError("bang")

        async def step_b(page, context):
            return {"never": "reached"}

        result = await engine.run([("a", step_a, {}), ("fail", step_fail, {}), ("b", step_b, {})])
        assert result.success is False
        assert len(result.steps) == 2

    @pytest.mark.asyncio
    async def test_step_result_has_fields(self) -> None:
        r = StepResult(name="test")
        assert r.status == StepStatus.PENDING
        assert r.error is None
        assert r.data == {}

    @pytest.mark.asyncio
    async def test_context_passed(self) -> None:
        page = AsyncMock()
        engine = WorkflowEngine(page, name="test")

        async def check_context(page, context, expected_key):
            assert context.get(expected_key) == "value"
            return {}

        result = await engine.run(
            [("check", check_context, {"expected_key": "my_key"})],
            my_key="value",
        )
        assert result.success is True


class TestApplicationConfig:
    def test_defaults(self) -> None:
        config = ApplicationConfig(apply_url="https://jobs.example.com")
        assert config.apply_url == "https://jobs.example.com"
        assert config.submit_selector != ""
        assert config.confirm_required is True

    def test_field_mapping(self) -> None:
        config = ApplicationConfig(
            apply_url="https://x.com",
            field_mapping={"name": "#name", "email": "#email"},
        )
        assert config.field_mapping["name"] == "#name"


class TestAutoApplyWorkflow:
    @pytest.mark.asyncio
    async def test_builds_workflow(self) -> None:
        config = ApplicationConfig(
            apply_url="https://example.com/apply",
            field_mapping={"name": "#full_name", "email": "#email"},
            resume_path="/tmp/resume.pdf",
        )
        page = AsyncMock()
        workflow = AutoApplyWorkflow(page, config)
        assert workflow is not None
