"""ATS platform detector — auto-identifies ATS from URL patterns and page content."""

import re
from dataclasses import dataclass
from enum import StrEnum


class ATSPlatform(StrEnum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKABLE = "workable"
    UNKNOWN = "unknown"


URL_PATTERNS: dict[str, re.Pattern[str]] = {
    ATSPlatform.GREENHOUSE: re.compile(r"boards\.greenhouse\.io|greenhouse\.io"),
    ATSPlatform.LEVER: re.compile(r"jobs\.lever\.co|lever\.co"),
    ATSPlatform.ASHBY: re.compile(r"jobs\.ashbyhq\.com|ashbyhq\.com"),
    ATSPlatform.WORKABLE: re.compile(r"apply\.workable\.com|workable\.com/api"),
}

PAGE_SIGNATURES: dict[str, list[str]] = {
    ATSPlatform.GREENHOUSE: ["greenhouse", "boards.greenhouse", "job-application"],
    ATSPlatform.LEVER: ["lever", "posting-page", "lever-jobs"],
    ATSPlatform.ASHBY: ["ashby", "ashby-posting", "posting-form"],
    ATSPlatform.WORKABLE: ["workable", "application-form", "apply-form"],
}

GREENHOUSE_PATTERNS = [
    re.compile(r"greenhouse"),
    re.compile(r"boards\.greenhouse"),
    re.compile(r"job_application"),
]

LEVER_PATTERNS = [
    re.compile(r"lever\.co"),
    re.compile(r"lever-jobs"),
]

ASHBY_PATTERNS = [
    re.compile(r"ashbyhq\.com"),
    re.compile(r"ashby-embed"),
]

WORKABLE_PATTERNS = [
    re.compile(r"workable\.com"),
    re.compile(r"workable-form"),
]


@dataclass
class PlatformDetection:
    platform: ATSPlatform
    confidence: float  # 0.0 - 1.0
    matched_by: str = ""


def detect_from_url(url: str) -> PlatformDetection:
    for platform, pattern in URL_PATTERNS.items():
        if pattern.search(url):
            return PlatformDetection(
                platform=ATSPlatform(platform), confidence=0.9, matched_by="url"
            )
    return PlatformDetection(platform=ATSPlatform.UNKNOWN, confidence=0.0)


def detect_from_page(url: str, content: str, page_title: str = "") -> PlatformDetection:
    url_detection = detect_from_url(url)
    if url_detection.confidence >= 0.9:
        return url_detection

    combined = f"{url} {content[:2000]} {page_title}".lower()

    platform_checks: list[tuple[ATSPlatform, list[re.Pattern[str]]]] = [
        (ATSPlatform.GREENHOUSE, GREENHOUSE_PATTERNS),
        (ATSPlatform.LEVER, LEVER_PATTERNS),
        (ATSPlatform.ASHBY, ASHBY_PATTERNS),
        (ATSPlatform.WORKABLE, WORKABLE_PATTERNS),
    ]

    for platform, patterns in platform_checks:
        matches = sum(1 for p in patterns if p.search(combined))
        if matches >= 2:
            return PlatformDetection(
                platform=platform,
                confidence=min(0.7 + matches * 0.1, 1.0),
                matched_by="content",
            )

    return PlatformDetection(platform=ATSPlatform.UNKNOWN, confidence=0.0)
