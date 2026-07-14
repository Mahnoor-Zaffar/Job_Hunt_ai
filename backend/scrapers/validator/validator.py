import logging
from typing import ClassVar

from backend.scrapers.models.models import NormalizedJob, ValidationResult

logger = logging.getLogger("job_hunting.validator")


class Validator:
    """Validates normalised job data before persistence.

    Checks required fields, data types, and basic quality constraints.
    Invalid jobs are flagged but not mutated.
    """

    REQUIRED_FIELDS: ClassVar[list[str]] = [
        "title",
        "company",
        "location",
        "url",
        "source",
        "source_id",
        "fingerprint",
    ]

    def validate(self, job: NormalizedJob) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        self._check_required(job, errors)
        self._check_urls(job, errors)
        self._check_salary(job, warnings)
        self._check_lengths(job, errors)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_batch(self, jobs: list[NormalizedJob]) -> list[ValidationResult]:
        return [self.validate(j) for j in jobs]

    def _check_required(self, job: NormalizedJob, errors: list[str]) -> None:
        for field in self.REQUIRED_FIELDS:
            value = getattr(job, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Missing required field: '{field}'")

    def _check_urls(self, job: NormalizedJob, errors: list[str]) -> None:
        if not job.url.startswith(("http://", "https://")):
            errors.append(f"Invalid url: '{job.url}'")
        if job.apply_url and not job.apply_url.startswith(("http://", "https://")):
            errors.append(f"Invalid apply_url: '{job.apply_url}'")

    def _check_salary(self, job: NormalizedJob, warnings: list[str]) -> None:
        if (
            job.salary_min is not None
            and job.salary_max is not None
            and job.salary_min > job.salary_max
        ):
            warnings.append(f"Salary min ({job.salary_min}) > max ({job.salary_max})")
        if (job.salary_min is not None or job.salary_max is not None) and not job.currency:
            warnings.append("Salary specified without currency")

    def _check_lengths(self, job: NormalizedJob, errors: list[str]) -> None:
        if len(job.title) > 500:
            errors.append("Title exceeds 500 characters")
        if len(job.company) > 500:
            errors.append("Company name exceeds 500 characters")
        if len(job.location) > 500:
            errors.append("Location exceeds 500 characters")
