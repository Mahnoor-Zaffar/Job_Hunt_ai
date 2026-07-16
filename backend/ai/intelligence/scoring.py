"""Multi-factor scoring engine — deterministic job matching.

Scores a candidate against a job across 10 dimensions.
Returns individual factor scores, weighted total, strengths, weaknesses,
missing skills, and recommendations — all without LLM calls.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("job_hunting.intelligence.scoring")

FACTOR_WEIGHTS = {
    "skills_overlap": 0.30,
    "experience_level": 0.15,
    "technologies": 0.15,
    "location": 0.10,
    "employment_type": 0.08,
    "salary": 0.08,
    "seniority": 0.07,
    "remote_preference": 0.05,
    "company_preference": 0.02,
}


@dataclass
class MatchResult:
    overall_score: float = 0.0
    factor_scores: dict[str, float] = field(default_factory=dict)
    skills_matched: list[str] = field(default_factory=list)
    skills_missing: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    deterministic: bool = True


class FactorScorer:
    def score(
        self,
        candidate_skills: list[str],
        job_skills: list[str] | None,
        candidate_experience_years: int | None,
        job_experience_level: str | None,
        candidate_location: str | None,
        job_location: str | None,
        candidate_remote: bool,
        job_remote: bool,
        candidate_employment: str | None,
        job_employment: str | None,
        candidate_salary_min: float | None,
        candidate_salary_max: float | None,
        job_salary_min: float | None,
        job_salary_max: float | None,
        candidate_watchlist: list[str] | None,
        job_company: str,
    ) -> MatchResult:
        skills_overlap = self._score_skills(candidate_skills, job_skills)
        experience = self._score_experience(candidate_experience_years, job_experience_level)
        techs = self._score_technologies(candidate_skills, job_skills)
        location = self._score_location(candidate_location, job_location)
        employment = self._score_employment(candidate_employment, job_employment)
        salary = self._score_salary(
            candidate_salary_min, candidate_salary_max, job_salary_min, job_salary_max
        )
        seniority = self._score_seniority(candidate_experience_years, job_experience_level)
        remote = self._score_remote(candidate_remote, job_remote)
        company = self._score_company(candidate_watchlist, job_company)

        factor_scores = {
            "skills_overlap": skills_overlap,
            "experience_level": experience,
            "technologies": techs,
            "location": location,
            "employment_type": employment,
            "salary": salary,
            "seniority": seniority,
            "remote_preference": remote,
            "company_preference": company,
        }

        overall = sum(factor_scores[k] * FACTOR_WEIGHTS.get(k, 0.1) for k in factor_scores)

        job_skill_set = {s.lower() for s in (job_skills or [])}
        cand_skill_set = {s.lower() for s in candidate_skills}
        matched = sorted(job_skill_set & cand_skill_set)
        missing = sorted(job_skill_set - cand_skill_set)

        strengths, weaknesses, recommendations = self._generate_insights(
            factor_scores, matched, missing
        )

        return MatchResult(
            overall_score=round(overall, 3),
            factor_scores={k: round(v, 3) for k, v in factor_scores.items()},
            skills_matched=matched,
            skills_missing=missing,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )

    def _score_skills(self, candidate: list[str], job: list[str] | None) -> float:
        if not job:
            return 0.5
        job_set = {s.lower() for s in job}
        cand_set = {s.lower() for s in candidate}
        if not job_set:
            return 0.5
        overlap = len(job_set & cand_set)
        ratio = overlap / len(job_set)
        return min(ratio, 1.0)

    def _score_experience(self, years: int | None, level: str | None) -> float:
        level_map = {"intern": 0, "junior": 1, "mid": 3, "senior": 5, "lead": 8, "executive": 12}
        if level is None:
            return 0.5
        required = level_map.get(level.lower(), 3)
        candidate_years = years or 0
        if candidate_years >= required:
            return 1.0
        if candidate_years >= required * 0.7:
            return 0.7
        if candidate_years >= required * 0.3:
            return 0.4
        return 0.1

    def _score_technologies(self, candidate: list[str], job: list[str] | None) -> float:
        return self._score_skills(candidate, job)

    def _score_location(self, candidate_loc: str | None, job_loc: str | None) -> float:
        if not candidate_loc or not job_loc:
            return 0.5
        c = candidate_loc.lower().strip()
        j = job_loc.lower().strip()
        if c == j:
            return 1.0
        c_parts = set(c.replace(",", " ").split())
        j_parts = set(j.replace(",", " ").split())
        if c_parts & j_parts:
            return 0.7
        return 0.3

    def _score_employment(self, candidate: str | None, job: str | None) -> float:
        if not candidate or not job:
            return 0.5
        return 1.0 if candidate.lower() == job.lower() else 0.2

    def _score_salary(
        self,
        c_min: float | None,
        c_max: float | None,
        j_min: float | None,
        j_max: float | None,
    ) -> float:
        if c_min is None or j_min is None:
            return 0.5
        if j_max and c_min > j_max:
            return 0.0
        if c_max and j_min > c_max:
            return 0.2
        if j_min <= c_min <= (j_max or j_min * 2):
            return 1.0
        return 0.5

    def _score_seniority(self, years: int | None, level: str | None) -> float:
        return self._score_experience(years, level)

    def _score_remote(self, candidate_remote: bool, job_remote: bool) -> float:
        if candidate_remote == job_remote:
            return 1.0
        if job_remote:
            return 0.5
        return 0.2

    def _score_company(self, watchlist: list[str] | None, company: str) -> float:
        if not watchlist:
            return 0.5
        if any(company.lower() in w.lower() for w in watchlist):
            return 1.0
        return 0.3

    def _generate_insights(
        self,
        scores: dict[str, float],
        matched: list[str],
        missing: list[str],
    ) -> tuple[list[str], list[str], list[str]]:
        strengths: list[str] = []
        weaknesses: list[str] = []
        recommendations: list[str] = []

        if scores["skills_overlap"] >= 0.7:
            strengths.append("Strong skills match with the role requirements")
        elif scores["skills_overlap"] < 0.3:
            weaknesses.append("Low skills overlap — consider upskilling")

        if matched:
            strengths.append(f"Matched skills: {', '.join(matched[:5])}")
        if missing:
            weaknesses.append(f"Missing skills: {', '.join(missing[:5])}")
            recommendations.append(f"Learn: {', '.join(missing[:3])}")

        if scores["experience_level"] >= 0.8:
            strengths.append("Experience level matches or exceeds requirements")
        elif scores["experience_level"] < 0.5:
            weaknesses.append("Experience level below requirements")

        if scores["location"] >= 1.0:
            strengths.append("Perfect location match")
        elif scores["location"] < 0.5:
            weaknesses.append("Location mismatch — relocation may be required")

        if scores["salary"] < 0.3:
            weaknesses.append("Salary expectation misalignment")

        if scores["remote_preference"] == 1.0:
            strengths.append("Remote work preference matches")

        if scores["company_preference"] == 1.0:
            strengths.append("Company on your watchlist")

        return strengths, weaknesses, recommendations
