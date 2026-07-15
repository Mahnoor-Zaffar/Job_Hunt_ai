"""Prometheus-compatible metrics for the Job Hunting platform.

Exposes counters, gauges, and histograms via a dedicated endpoint.
Integrates with the scraper framework and API layer to track:
- Jobs scraped / new / duplicate
- Scraper duration / success / failure
- API request count / latency / status codes
- Active jobs count

Requires ``prometheus_client`` to be installed.
"""

import logging
from typing import Any

logger = logging.getLogger("job_hunting.metrics")

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

    class _FakeMetric:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def labels(self, **_: Any) -> "_FakeMetric":
            return self

        def inc(self, amount: int = 1) -> None:
            pass

        def set(self, value: float) -> None:
            pass

        def dec(self, amount: int = 1) -> None:
            pass

        def observe(self, value: float) -> None:
            pass

    Counter = _FakeMetric
    Gauge = _FakeMetric
    Histogram = _FakeMetric

    def generate_latest(*args: Any, **kwargs: Any) -> bytes:
        return b"# prometheus_client not installed\n"


# -- Metric definitions ----------------------------------------------------

jobs_scraped_total = Counter(
    "jobhunting_jobs_scraped_total",
    "Total number of jobs scraped",
    ["source"],
)

jobs_new_total = Counter(
    "jobhunting_jobs_new_total",
    "Total number of new (non-duplicate) jobs",
    ["source"],
)

scraper_runs_total = Counter(
    "jobhunting_scraper_runs_total",
    "Total scraper executions",
    ["source", "status"],
)

scraper_duration_seconds = Histogram(
    "jobhunting_scraper_duration_seconds",
    "Scraper execution duration in seconds",
    ["source"],
)

api_requests_total = Counter(
    "jobhunting_api_requests_total",
    "Total API requests",
    ["method", "path", "status_code"],
)

api_request_duration_seconds = Histogram(
    "jobhunting_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "path"],
)

active_jobs_gauge = Gauge(
    "jobhunting_active_jobs",
    "Number of currently active jobs",
)

scraper_failures_total = Counter(
    "jobhunting_scraper_failures_total",
    "Total scraper failures",
    ["source"],
)


# -- Helpers ---------------------------------------------------------------


def record_scraper_run(source: str, success: bool, duration: float) -> None:
    scraper_runs_total.labels(source=source, status="success" if success else "failure").inc()
    scraper_duration_seconds.labels(source=source).observe(duration)
    if not success:
        scraper_failures_total.labels(source=source).inc()


def record_api_request(method: str, path: str, status_code: int, duration: float) -> None:
    api_requests_total.labels(method=method, path=path, status_code=str(status_code)).inc()
    api_request_duration_seconds.labels(method=method, path=path).observe(duration)


def get_metrics() -> bytes:
    return generate_latest()  # type: ignore[no-any-return]
