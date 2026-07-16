"""AI Application Assistant — generates answers for common application questions.

Uses the AI platform to produce grounded, honest answers based on the
candidate's resume, profile, and the target job description.
"""

import logging

from backend.ai.career_assistant import CareerAssistant
from backend.models.job import Job

logger = logging.getLogger("job_hunting.automation.assist")

STANDARD_QUESTIONS = [
    "motivation",
    "why_company",
    "why_role",
    "salary_expectations",
    "notice_period",
    "relocation",
    "sponsorship",
    "work_authorization",
    "availability",
    "strengths",
    "weaknesses",
    "achievement",
]


class ApplicationAssistant:
    def __init__(self, ai: CareerAssistant | None = None) -> None:
        self._ai = ai or CareerAssistant()

    async def generate_answers(
        self,
        job: Job,
        candidate_profile: str,
        questions: list[str] | None = None,
    ) -> dict[str, str]:
        target_questions = questions or STANDARD_QUESTIONS
        answers: dict[str, str] = {}

        for question in target_questions:
            answer = await self._answer_question(question, job, candidate_profile)
            answers[question] = answer or ""

        return answers

    async def _answer_question(self, question: str, job: Job, candidate_profile: str) -> str:
        context = self._build_context(question, job)

        try:
            result = await self._ai._ai.generate_text(
                "application.short_answer",
                {
                    "question": context[:500],
                    "candidate_profile": candidate_profile[:2000],
                    "job_title": job.title,
                    "company": job.company,
                },
                temperature=0.5,
                max_tokens=300,
            )
            return result
        except Exception as exc:
            logger.warning("AI answer generation failed for '%s': %s", question, exc)
            return ""

    def _build_context(self, question: str, job: Job) -> str:
        prompts: dict[str, str] = {
            "motivation": f"Why are you interested in the {job.title} role at {job.company}?",
            "why_company": f"Why do you want to work at {job.company}?",
            "why_role": f"Why are you a good fit for the {job.title} position?",
            "salary_expectations": f"What are your salary expectations for the {job.title} role at {job.company}? Location: {job.location}",
            "notice_period": "What is your notice period or availability to start?",
            "relocation": f"Are you willing to relocate to {job.location}?",
            "sponsorship": f"Do you require visa sponsorship to work in {job.location}?",
            "work_authorization": f"Are you legally authorized to work in {job.location}?",
            "availability": "When are you available to start?",
            "strengths": f"What are your key strengths relevant to {job.title}?",
            "weaknesses": "Describe a professional weakness and how you're improving it.",
            "achievement": "Describe your most significant professional achievement.",
        }
        return prompts.get(question, question)
