import uuid

from backend.models.career_profile import CareerProfile
from backend.repositories.career_profile import CareerProfileRepository


class CareerProfileService:
    def __init__(self, repo: CareerProfileRepository) -> None:
        self._repo = repo

    async def get(self, user_id: uuid.UUID) -> CareerProfile | None:
        return await self._repo.get_by_user(user_id)

    async def create_or_update(self, user_id: uuid.UUID, data: dict) -> CareerProfile:
        existing = await self._repo.get_by_user(user_id)
        if existing:
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return await self._repo.update(existing)
        profile = CareerProfile(user_id=user_id, **data)
        return await self._repo.create(profile)

    async def regenerate_skills(self, user_id: uuid.UUID) -> CareerProfile:
        profile = await self._repo.get_by_user(user_id)
        if not profile or not profile.resume_text:
            raise ValueError("No resume text to parse")
        text = profile.resume_text.lower()
        common_tech = [
            "python", "javascript", "typescript", "java", "go", "rust", "c++", "ruby",
            "react", "angular", "vue", "node.js", "express.js", "django", "flask", "fastapi",
            "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible",
            "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch",
            "graphql", "rest", "grpc", "websocket", "kafka", "rabbitmq",
            "git", "ci/cd", "jenkins", "github actions", "pytest", "jest",
            "machine learning", "deep learning", "nlp", "llm", "langchain", "pytorch", "tensorflow",
            "sql", "nosql", "linux", "bash", "nginx", "html", "css", "tailwind",
        ]
        found = set()
        for tech in common_tech:
            if tech in text:
                found.add(tech)
        profile.skills = sorted(found) if found else profile.skills
        if found:
            profile.tech_stack = sorted(found)
        return await self._repo.update(profile)
