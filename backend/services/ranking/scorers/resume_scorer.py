from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class ResumeScorer(BaseScorer):
    name = "resume_match"
    max_score = 35.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        if not profile.resume_text:
            return FactorScore(name=self.name, score=0, max_score=self.max_score, details={"reason": "No resume text"})

        resume_lower = profile.resume_text.lower()
        target_text = f"{job.title or ''} {job.description or ''} {job.requirements or ''}".lower()
        job_skills_text = " ".join(s.lower() for s in (job.skills or []))

        all_matched: list[str] = []

        resume_words = {w for w in resume_lower.split() if len(w) > 3}
        if target_text:
            words_matched = [w for w in resume_words if w in target_text]
            all_matched.extend(words_matched)

        resume_skills = {s.lower() for s in (profile.skills or [])}
        if job_skills_text:
            skills_matched = [s for s in resume_skills if s in job_skills_text or s in target_text]
            all_matched.extend(skills_matched)

        unique_matched = list(set(all_matched))

        word_score = len(unique_matched) / max(len(resume_words | resume_skills), 1) if resume_words or resume_skills else 0
        score = round(word_score * self.max_score, 1)
        score = min(score, self.max_score)

        return FactorScore(
            name=self.name,
            score=score,
            max_score=self.max_score,
            details={"matched": unique_matched[:25], "overlap_pct": round(word_score * 100, 1)},
        )
