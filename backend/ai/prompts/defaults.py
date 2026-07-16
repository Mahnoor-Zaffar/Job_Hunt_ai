"""Default prompts — versioned, documented, testable."""

from backend.ai.prompts.registry import PromptRegistry

_prompts = PromptRegistry()

# Resume parsing
_prompts.add_version(
    "resume.extract",
    """Extract structured data from this resume. Return ONLY valid JSON.

Keys:
- full_name, email, phone, location, summary
- skills (list of strings)
- experiences (list of {title, company, dates, highlights})
- education (list of {degree, school, year})
- certifications (list of strings)
- languages (list of strings)

Resume text:
$resume_text""",
    description="Extract structured data from resume text",
    tags=["resume", "extraction", "json"],
)

# Resume optimisation
_prompts.add_version(
    "resume.optimise",
    """Rewrite this resume to better match the job description.
Focus on relevant skills and experience. Do not invent qualifications.

Job Description:
$job_description

Resume Content:
$resume_text

Return ONLY the rewritten resume with bullet points.""",
    description="Optimize resume for a specific job",
    tags=["resume", "generation"],
)

# Cover letter
_prompts.add_version(
    "cover_letter.generate",
    """Write a professional cover letter (200-400 words).

Job Title: $job_title
Company: $company
Job Description:
$job_description

Candidate Profile:
$candidate_profile

Additional Notes: $notes

Use a professional tone. Address to Hiring Manager.
2-3 body paragraphs connecting experience to requirements.
Do not include placeholders.""",
    description="Generate tailored cover letter",
    tags=["cover_letter", "generation"],
)

# Job matching
_prompts.add_version(
    "job.match",
    """Compare this candidate against the job. Return ONLY valid JSON.

Keys: match_score (0.0-1.0), skills_match, skills_missing,
strengths, weaknesses, fit_summary

Candidate: $candidate_profile
Job: $job_title at $company
Description: $job_description
Skills: $skills""",
    description="Score candidate fit for a job",
    tags=["matching", "json"],
)

# Skill gap
_prompts.add_version(
    "skill_gap.analyse",
    """Analyse the skill gap. Return ONLY valid JSON.

Keys: matching_skills, missing_skills, partial_skills,
priority_order, estimated_timeframe, learning_resources, summary

Current skills: $current_skills
Target role: $target_role
Required skills: $required_skills
Job description: $job_description""",
    description="Analyze skill gaps and recommend learning",
    tags=["skills", "json"],
)

# Interview questions
_prompts.add_version(
    "interview.questions",
    """Generate 5 technical and 3 behavioral interview questions
for this role. Include brief expected answers.

Role: $job_title
Company: $company
Description: $job_description""",
    description="Generate interview preparation questions",
    tags=["interview", "generation"],
    version=1,
)

# Company research
_prompts.add_version(
    "company.research",
    """Summarize what this company does, its industry, size,
culture, and recent news in 2-3 paragraphs.

Company: $company_name
Additional context: $context""",
    description="Research and summarize a company",
    tags=["company", "research"],
)


def get_prompt_registry() -> PromptRegistry:
    return _prompts
