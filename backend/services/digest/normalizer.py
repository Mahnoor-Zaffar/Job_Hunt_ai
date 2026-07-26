from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from backend.services.digest.models import NormalizedJob


def normalize_job(raw: Any) -> NormalizedJob:
    if isinstance(raw, NormalizedJob):
        return raw

    if hasattr(raw, "_sa_instance_state") or hasattr(raw, "__table__"):
        return _from_orm(raw)

    if isinstance(raw, dict):
        return _from_dict(raw)

    raise TypeError(f"Cannot normalize job of type {type(raw)}")


def _from_orm(obj: Any) -> NormalizedJob:
    def _val(field: str, default=None):
        return getattr(obj, field, default)

    skills_raw = _val("skills")
    if skills_raw is None:
        skills_list = None
    elif isinstance(skills_raw, list):
        skills_list = [s.lower().strip() for s in skills_raw]
    else:
        skills_list = None

    salary_min = _val("salary_min")
    if salary_min is not None and not isinstance(salary_min, Decimal):
        salary_min = Decimal(str(salary_min))

    salary_max = _val("salary_max")
    if salary_max is not None and not isinstance(salary_max, Decimal):
        salary_max = Decimal(str(salary_max))

    posted_at = _val("posted_at")
    if posted_at and isinstance(posted_at, str):
        try:
            posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            posted_at = None
    if posted_at and posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)

    return NormalizedJob(
        id=str(_val("id", "")),
        title=_val("title", ""),
        company=_val("company", ""),
        company_url=_val("company_url"),
        location=_val("location"),
        city=_val("city"),
        country=_val("country"),
        is_remote=_val("is_remote", False),
        remote_type=_val("remote_type", "onsite"),
        description=_val("description"),
        requirements=_val("requirements"),
        url=_val("url", ""),
        apply_url=_val("apply_url"),
        source=_val("source", ""),
        source_id=_val("source_id", ""),
        salary_min=salary_min,
        salary_max=salary_max,
        currency=_val("currency"),
        employment_type=_val("employment_type"),
        experience_level=_val("experience_level"),
        skills=skills_list,
        posted_at=posted_at,
    )


def _from_dict(d: dict[str, Any]) -> NormalizedJob:
    skills_raw = d.get("skills")
    if skills_raw is None:
        skills_list = None
    elif isinstance(skills_raw, list):
        skills_list = [s.lower().strip() for s in skills_raw]
    else:
        skills_list = None

    salary_min = d.get("salary_min")
    if salary_min is not None and not isinstance(salary_min, Decimal):
        salary_min = Decimal(str(salary_min))

    salary_max = d.get("salary_max")
    if salary_max is not None and not isinstance(salary_max, Decimal):
        salary_max = Decimal(str(salary_max))

    posted_at = d.get("posted_at")
    if posted_at and isinstance(posted_at, str):
        try:
            posted_at = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            posted_at = None
    if posted_at and posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)

    return NormalizedJob(
        id=str(d.get("id", "")),
        title=d.get("title", ""),
        company=d.get("company", ""),
        company_url=d.get("company_url"),
        location=d.get("location"),
        city=d.get("city"),
        country=d.get("country"),
        is_remote=d.get("is_remote", False),
        remote_type=d.get("remote_type", "onsite"),
        description=d.get("description"),
        requirements=d.get("requirements"),
        url=d.get("url", ""),
        apply_url=d.get("apply_url"),
        source=d.get("source", ""),
        source_id=d.get("source_id", ""),
        salary_min=salary_min,
        salary_max=salary_max,
        currency=d.get("currency"),
        employment_type=d.get("employment_type"),
        experience_level=d.get("experience_level"),
        skills=skills_list,
        posted_at=posted_at,
    )
