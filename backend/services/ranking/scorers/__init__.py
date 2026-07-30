from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.scorers.classifier_scorer import ClassifierScorer
from backend.services.ranking.scorers.company_scorer import CompanyScorer
from backend.services.ranking.scorers.experience_level_scorer import ExperienceLevelScorer
from backend.services.ranking.scorers.location_scorer import LocationScorer
from backend.services.ranking.scorers.posted_date_scorer import PostedDateScorer
from backend.services.ranking.scorers.resume_scorer import ResumeScorer
from backend.services.ranking.scorers.salary_scorer import SalaryScorer
from backend.services.ranking.scorers.skill_scorer import SkillScorer
from backend.services.ranking.scorers.sponsorship_scorer import SponsorshipScorer

REGISTRY: list[type[BaseScorer]] = [
    ResumeScorer,
    SkillScorer,
    CompanyScorer,
    LocationScorer,
    ExperienceLevelScorer,
    SalaryScorer,
    PostedDateScorer,
    SponsorshipScorer,
    ClassifierScorer,
]
