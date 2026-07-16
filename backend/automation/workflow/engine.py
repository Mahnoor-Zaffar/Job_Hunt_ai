"""Workflow engine — composable, retryable automation pipelines.

Each workflow is a sequence of steps.  Steps can be retried,
have timeouts, and emit events.  Workflows are reusable across
different ATS platforms by swapping step configurations.
"""

import contextlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from playwright.async_api import Page

logger = logging.getLogger("job_hunting.automation.workflow")


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    name: str
    status: StepStatus = StepStatus.PENDING
    duration_ms: float = 0.0
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    retries: int = 0


@dataclass
class WorkflowResult:
    name: str
    steps: list[StepResult] = field(default_factory=list)
    success: bool = False
    total_duration_ms: float = 0.0

    @property
    def failed_steps(self) -> list[StepResult]:
        return [s for s in self.steps if s.status == StepStatus.FAILED]


StepFn = Callable[..., Any]


class WorkflowEngine:
    def __init__(self, page: Page, name: str = "workflow") -> None:
        self._page = page
        self._name = name
        self._context: dict[str, Any] = {}
        self._on_step_complete: list[Callable[[StepResult], None]] = []

    def on_step(self, callback: Callable[[StepResult], None]) -> None:
        self._on_step_complete.append(callback)

    def set_context(self, **kwargs: Any) -> None:
        self._context.update(kwargs)

    def get_context(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    async def run(
        self, steps: list[tuple[str, StepFn, dict[str, Any] | None]], **ctx: Any
    ) -> WorkflowResult:
        self._context.update(ctx)
        result = WorkflowResult(name=self._name)
        start = time.perf_counter()

        for step_name, step_fn, step_kwargs in steps:
            step_result = await self._execute_step(step_name, step_fn, step_kwargs or {})

            if step_result.status == StepStatus.FAILED:
                result.steps.append(step_result)
                result.total_duration_ms = (time.perf_counter() - start) * 1000
                return result

            result.steps.append(step_result)

        result.success = True
        result.total_duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Workflow '%s' completed: %d/%d steps succeeded in %.0fms",
            self._name,
            sum(1 for s in result.steps if s.status == StepStatus.SUCCESS),
            len(result.steps),
            result.total_duration_ms,
        )
        return result

    async def _execute_step(self, name: str, fn: StepFn, kwargs: dict[str, Any]) -> StepResult:
        result = StepResult(name=name, status=StepStatus.RUNNING)
        start = time.perf_counter()

        try:
            merged = {**kwargs, "page": self._page, "context": self._context}
            result.data = await fn(**merged) or {}
            result.status = StepStatus.SUCCESS
        except Exception as exc:
            result.status = StepStatus.FAILED
            result.error = str(exc)
            logger.error("Step '%s' failed: %s", name, exc)

        result.duration_ms = (time.perf_counter() - start) * 1000

        for callback in self._on_step_complete:
            with contextlib.suppress(Exception):
                callback(result)

        return result


async def step_navigate(page: Page, context: dict[str, Any], url: str, **_: Any) -> dict[str, Any]:
    from backend.automation.workflow.actions import navigate

    ok = await navigate(page, url)
    if not ok:
        raise RuntimeError(f"Failed to navigate to {url}")
    context["current_url"] = url
    return {"url": url}


async def step_wait(
    page: Page, context: dict[str, Any], selector: str, timeout: int = 10000, **_: Any
) -> dict[str, Any]:
    from backend.automation.workflow.actions import wait_for_selector

    ok = await wait_for_selector(page, selector, timeout=timeout)
    if not ok:
        raise RuntimeError(f"Selector not found: {selector}")
    return {"selector": selector}


async def step_click(
    page: Page, context: dict[str, Any], selector: str, **_: Any
) -> dict[str, Any]:
    from backend.automation.workflow.actions import click

    ok = await click(page, selector)
    if not ok:
        raise RuntimeError(f"Failed to click: {selector}")
    return {"clicked": selector}


async def step_fill(
    page: Page, context: dict[str, Any], selector: str, value: str, **_: Any
) -> dict[str, Any]:
    from backend.automation.workflow.actions import fill_field

    ok = await fill_field(page, selector, value)
    if not ok:
        raise RuntimeError(f"Failed to fill: {selector}")
    return {"filled": selector, "value": value}


async def step_upload(
    page: Page, context: dict[str, Any], selector: str, file_path: str, **_: Any
) -> dict[str, Any]:
    from backend.automation.workflow.actions import upload_file

    ok = await upload_file(page, selector, file_path)
    if not ok:
        raise RuntimeError(f"Failed to upload: {selector}")
    return {"uploaded": selector, "file": file_path}


async def step_extract(
    page: Page, context: dict[str, Any], selector: str, **_: Any
) -> dict[str, Any]:
    from backend.automation.workflow.actions import extract_text

    text = await extract_text(page, selector)
    if text:
        context["extracted"] = text
    return {"selector": selector, "text": text}


async def step_screenshot(
    page: Page, context: dict[str, Any], name: str, **_: Any
) -> dict[str, Any]:
    path = f"screenshots/{name}_{int(time.time())}.png"
    await page.screenshot(path=path, full_page=True)
    return {"screenshot": path}
