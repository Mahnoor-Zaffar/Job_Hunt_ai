from __future__ import annotations

import logging

from backend.models.github_repo import GitHubRepo

logger = logging.getLogger("job_hunting.project_matcher")


_HIGHLIGHT_REPOS = {"tayari.ai", "tayari-ai", "tayari_ai", "tayariai"}
_OS_REPOS = {"sktime", "pandas", "napari", "node"}


def match_best_repo(repos: list[GitHubRepo], job_title: str, job_description: str) -> GitHubRepo | None:
    if not repos:
        return None

    title_lower = job_title.lower()
    desc_lower = (job_description or "").lower()

    highlight = _find_by_name(repos, _HIGHLIGHT_REPOS)
    if highlight and _has_tech_overlap(highlight, desc_lower):
        return highlight

    scored: list[tuple[int, GitHubRepo]] = []
    for repo in repos:
        score = _score_repo(repo, title_lower, desc_lower)
        if score > 0:
            scored.append((score, repo))

    scored.sort(key=lambda x: (-x[0], -x[1].stars))

    if scored:
        return scored[0][1]

    if highlight:
        return highlight

    return repos[0] if repos else None


def get_matching_open_source(repos: list[GitHubRepo]) -> list[str]:
    matched: list[str] = []
    for repo in repos:
        if repo.repo_name.lower() in _OS_REPOS:
            matched.append(repo.repo_name)
    return matched


def _find_by_name(repos: list[GitHubRepo], names: set[str]) -> GitHubRepo | None:
    for repo in repos:
        if repo.repo_name.lower() in names:
            return repo
    return None


def _score_repo(repo: GitHubRepo, title_lower: str, desc_lower: str) -> int:
    score = 0

    if repo.language and (
        repo.language.lower() in desc_lower or repo.language.lower() in title_lower
    ):
        score += 3

    for topic in (repo.topics or []):
        if topic.lower() in desc_lower or topic.lower() in title_lower:
            score += 2

    desc_words = (repo.description or "").lower().split()
    for word in desc_words:
        if len(word) > 3 and word in desc_lower:
            score += 1

    return score


def _has_tech_overlap(repo: GitHubRepo, desc_lower: str) -> bool:
    if repo.language and repo.language.lower() in desc_lower:
        return True
    for topic in (repo.topics or []):
        if topic.lower() in desc_lower:
            return True
    return False


def _repo_text(repo: GitHubRepo) -> str:
    parts = [repo.repo_name.lower(), (repo.description or "").lower()]
    parts.extend((t or "").lower() for t in (repo.topics or []))
    if repo.readme_text:
        parts.append(repo.readme_text.lower())
    return " ".join(parts)
