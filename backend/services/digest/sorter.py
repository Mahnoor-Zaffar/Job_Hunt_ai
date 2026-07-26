from datetime import datetime, timezone
from backend.services.digest.models import ScoredJob


def sort_jobs(jobs: list[ScoredJob]) -> list[ScoredJob]:
    return sorted(
        jobs,
        key=_sort_key,
        reverse=True,
    )


def _sort_key(sj: ScoredJob) -> tuple:
    confidence_order = {"high": 3, "medium": 2, "low": 1}
    conf_value = confidence_order.get(sj.confidence, 0)

    posted = sj.job.posted_at
    if posted is None:
        posted_ts = 0.0
    else:
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        posted_ts = posted.timestamp()

    salary = float(sj.job.salary_min) if sj.job.salary_min else 0.0

    return (conf_value, posted_ts, salary)
