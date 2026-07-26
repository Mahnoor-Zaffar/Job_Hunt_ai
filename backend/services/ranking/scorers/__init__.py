from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.scorers.classifier_scorer import ClassifierScorer
from backend.services.ranking.scorers.company_scorer import CompanyScorer
from backend.services.ranking.scorers.freshness_scorer import FreshnessScorer
from backend.services.ranking.scorers.location_scorer import LocationScorer
from backend.services.ranking.scorers.resume_scorer import ResumeScorer
from backend.services.ranking.scorers.salary_scorer import SalaryScorer
from backend.services.ranking.scorers.skill_scorer import SkillScorer

REGISTRY: list[type[BaseScorer]] = [
    ResumeScorer,
    SkillScorer,
    CompanyScorer,
    LocationScorer,
    ClassifierScorer,
    SalaryScorer,
    FreshnessScorer,
]
