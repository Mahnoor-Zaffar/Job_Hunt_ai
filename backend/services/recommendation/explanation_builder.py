from backend.models.career_profile import CareerProfile
from backend.services.ranking.models import RankedJob
from backend.services.recommendation.models import WhyExplanation


def build_explanation(ranked: RankedJob, profile: CareerProfile | None = None) -> WhyExplanation:
    strengths: list[str] = []
    weaknesses: list[str] = []
    missing_skills: list[str] = []
    recommendations: list[str] = []

    for factor in ranked.factors:
        pct = factor.score / factor.max_score if factor.max_score > 0 else 0
        details = factor.details or {}

        if pct >= 0.8:
            if factor.name == "resume_match":
                matched = details.get("matched", [])
                if matched:
                    strengths.append(f"Resume matches keywords: {', '.join(matched[:5])}")
                else:
                    strengths.append(f"Resume alignment strong (+{factor.score:.0f})")
            elif factor.name == "skills_overlap":
                matched = details.get("matched", [])
                if matched:
                    strengths.append(f"Skills match: {', '.join(matched[:5])}")
                else:
                    strengths.append("Strong skill overlap")
            elif factor.name == "location_preference":
                reason = details.get("reason", "Location matches")
                strengths.append(reason)
            elif factor.name == "salary_attractiveness":
                verdict = details.get("verdict", "good")
                strengths.append(f"Salary {verdict} (${details.get('job_salary', 0):.0f})")
            elif factor.name == "company_quality":
                if details.get("preferred"):
                    strengths.append("Company is in your preferred list")
                else:
                    strengths.append("Company quality is good")
            elif factor.name == "classifier_confidence":
                cat = details.get("category", "")
                strengths.append(f"Strong category match ({cat})" if cat else "Strong classifier confidence")
            elif factor.name == "freshness":
                age = details.get("age_days")
                if age is not None and age < 7:
                    strengths.append(f"Recently posted ({age:.0f} days ago)")

        elif pct <= 0.3 and factor.max_score > 0:
            if factor.name == "skills_overlap":
                missing = details.get("missing", [])
                missing_skills.extend(missing)
                if missing:
                    weaknesses.append(f"Missing skills: {', '.join(missing[:5])}")
                if missing:
                    recommendations.append(f"Learn {', '.join(missing[:3])}")
            elif factor.name == "salary_attractiveness":
                verdict = details.get("verdict", "low")
                weaknesses.append(f"Salary {verdict} (${details.get('job_salary', 0):.0f})")
                recommendations.append("Negotiate salary or find higher-paying roles")
            elif factor.name == "location_preference":
                reason = details.get("reason", "Location mismatch")
                weaknesses.append(reason)
            elif factor.name == "freshness":
                age = details.get("age_days")
                if age is not None and age > 14:
                    weaknesses.append(f"Posted {age:.0f} days ago (may be stale)")

    if missing_skills:
        recommendations.append(f"Tailor resume to highlight {', '.join(missing_skills[:3])}")

    if profile and profile.resume_text and ranked.job.description:
        recommendations.append("Contact recruiter to express interest")

    return WhyExplanation(
        strengths=strengths,
        weaknesses=weaknesses,
        missing_skills=missing_skills,
        recommendations=recommendations,
    )
