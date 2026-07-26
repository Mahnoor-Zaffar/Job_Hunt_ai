from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


class MatchResult(Enum):
    ACCEPTED = "accepted"
    REJECTED_TITLE = "rejected_title"
    REJECTED_KEYWORD = "rejected_keyword"
    REJECTED_INTERNSHIP = "rejected_internship"
    REJECTED_LOW_SCORE = "rejected_low_score"
    REJECTED_TECH = "rejected_tech"
    REJECTED_OLD = "rejected_old"


@dataclass
class Explanation:
    result: MatchResult
    reason: str
    matched_title: str | None = None
    matched_skills: list[str] = field(default_factory=list)
    matched_category: str | None = None
    score: int = 0


@dataclass
class NormalizedJob:
    id: str
    title: str
    company: str
    company_url: str | None = None
    location: str | None = None
    city: str | None = None
    country: str | None = None
    is_remote: bool = False
    remote_type: str = "onsite"
    description: str | None = None
    requirements: str | None = None
    url: str = ""
    apply_url: str | None = None
    source: str = ""
    source_id: str = ""
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    skills: list[str] | None = None
    posted_at: datetime | None = None


@dataclass
class ClassificationResult:
    accepted: bool
    category: str | None
    confidence: str
    matched_title: str | None
    matched_technologies: list[str]
    reason: str


@dataclass
class ScoredJob:
    job: NormalizedJob
    score: int = 0
    confidence: str = "low"
    category: str | None = None
    explanation: Explanation | None = None


@dataclass
class CategoryGroup:
    category_key: str
    category_label: str
    jobs: list[ScoredJob]


@dataclass
class PipelineResult:
    total_scraped: int = 0
    accepted: int = 0
    rejected: int = 0
    duplicates_removed: int = 0
    processing_duration_ms: float = 0.0
    email_generation_ms: float = 0.0
    email_delivered: bool = False
    email_error: str | None = None
    categories: list[CategoryGroup] = field(default_factory=list)
    explanations: list[Explanation] = field(default_factory=list)
    acceptance_rate: float = 0.0
    per_category_stats: dict[str, int] = field(default_factory=dict)
