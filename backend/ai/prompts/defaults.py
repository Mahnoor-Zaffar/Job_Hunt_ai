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


# Interview — technical questions
_prompts.add_version(
    "interview.technical",
    """Generate 5 technical interview questions for this role.
Return ONLY valid JSON with key "questions" (list of {question, expected_answer, difficulty, topic}).

Role: $job_title
Description: $job_description
Skills: $skills""",
    description="Generate technical interview questions",
    tags=["interview", "technical", "json"],
)

# Interview — behavioral questions
_prompts.add_version(
    "interview.behavioral",
    """Generate 5 behavioral interview questions for this role using the STAR method.
Return ONLY valid JSON with key "questions" (list of {question, context, suggested_approach}).

Role: $job_title
Company: $company
Seniority: $experience_level""",
    description="Generate behavioral interview questions",
    tags=["interview", "behavioral", "json"],
)

# Interview — company-specific
_prompts.add_version(
    "interview.company",
    """Generate 3 company-specific questions the interviewer might ask about this company.
Include what to research and a suggested answer approach.
Return ONLY valid JSON with key "questions" (list of {question, research_tip, suggested_answer}).

Company: $company""",
    description="Generate company-specific interview questions",
    tags=["interview", "company", "json"],
)

# Interview — follow-up
_prompts.add_version(
    "interview.follow_up",
    """Based on this job, generate 3 smart questions the candidate should ask the interviewer.
Return ONLY valid JSON with key "questions" (list of {question, purpose}).

Role: $job_title
Company: $company""",
    description="Generate smart follow-up questions to ask",
    tags=["interview", "follow-up", "json"],
)

# Application — short answers
_prompts.add_version(
    "application.short_answer",
    """Write a concise (50-100 word) answer to this application question.
Ground the response in the candidate's actual experience.

Question: $question
Candidate Profile: $candidate_profile
Job: $job_title at $company""",
    description="Generate short application answers",
    tags=["application", "short"],
)

# Application — motivation statement
_prompts.add_version(
    "application.motivation",
    """Write a compelling motivation statement (100-150 words) for this role.
Explain why the candidate wants to work at this company in this role.
Ground in the candidate's actual background.

Company: $company
Job Title: $job_title
Job Description: $job_description
Candidate Profile: $candidate_profile""",
    description="Generate motivation statement",
    tags=["application", "motivation"],
)

# Application — salary guidance
_prompts.add_version(
    "application.salary",
    """Provide salary negotiation guidance for this role.
Return ONLY valid JSON with keys: suggested_range, market_average, negotiation_tips (list), talking_points (list).

Role: $job_title
Location: $location
Experience Level: $experience_level
Skills: $skills""",
    description="Generate salary negotiation guidance",
    tags=["application", "salary", "json"],
)

# Application — relocation response
_prompts.add_version(
    "application.relocation",
    """Write a brief (50-75 word) professional response about relocation willingness.
Be honest but positive.

Job Location: $job_location
Candidate Location: $candidate_location
Remote Status: $remote_status""",
    description="Generate relocation response",
    tags=["application", "relocation"],
)

# Career — job summary
_prompts.add_version(
    "career.job_summary",
    """Summarize this job posting in 3-4 bullet points covering:
role, key requirements, tech stack, and what makes it interesting.
Return ONLY valid JSON with key "summary" (list of strings).

Title: $job_title
Company: $company
Description: $job_description""",
    description="Summarize a job posting",
    tags=["career", "summary", "json"],
)

# Career — company summary
_prompts.add_version(
    "career.company_summary",
    """Summarize what this company does, its industry focus, culture,
and why it might be interesting to work there. 2-3 paragraphs.

Company: $company_name""",
    description="Summarize a company for job seekers",
    tags=["career", "company"],
)

# Career — technology demand
_prompts.add_version(
    "career.tech_demand",
    """Analyze the demand for these technologies in the current job market.
Return ONLY valid JSON with key "technologies" (list of {name, demand_level, trend, notes}).

Technologies: $technologies""",
    description="Analyze technology demand trends",
    tags=["career", "tech", "json"],
)

# Resume — bullet point rewriting
_prompts.add_version(
    "resume.rewrite_bullets",
    """Rewrite these resume bullet points to be more impactful.
Use strong action verbs and quantify achievements where possible.
Do NOT invent experiences the candidate doesn't have.

Original Bullets:
$bullets

Return ONLY the rewritten bullet points, one per line.""",
    description="Rewrite resume bullet points for impact",
    tags=["resume", "rewrite"],
)

# Resume — keyword suggestions
_prompts.add_version(
    "resume.suggest_keywords",
    """Based on this job description, suggest 8-10 keywords the candidate
should include in their resume to improve ATS matching.
Return ONLY valid JSON with key "keywords" (list of strings).

Job Description:
$job_description

Current Resume Skills: $current_skills""",
    description="Suggest missing resume keywords",
    tags=["resume", "keywords", "json"],
)


# Career — company deep research
_prompts.add_version(
    "career.company_research",
    """Research this company for a job seeker. Return ONLY valid JSON.
Keys: ai_strategy (company AI/tech direction), engineering_culture,
recent_moves (funding, layoffs, expansions), interview_tips (2-3 tips),
red_flags (any concerns), why_interested (why someone would want to work here).

Company: $company_name""",
    description="Deep company research for job seekers",
    tags=["career", "research", "json"],
)

# Career — contact discovery
_prompts.add_version(
    "career.contact_discovery",
    """For this company and role, suggest who to contact on LinkedIn.
Return ONLY valid JSON.
Keys: likely_roles (titles to search for, e.g. 'Engineering Manager'),
linkedin_search_tips (search queries to use),
approach_angle (why you'd be valuable to them).

Company: $company_name
Job Title: $job_title""",
    description="Discover hiring managers and contacts",
    tags=["career", "contacts", "json"],
)

# Career — LinkedIn message draft
_prompts.add_version(
    "career.linkedin_message",
    """Write a concise LinkedIn connection message (≤300 characters).
Be genuine and professional. Mention specific interest in the company.

Company: $company
Role: $role
Contact type: $contact_type
Context: $context""",
    description="Draft LinkedIn outreach messages",
    tags=["career", "linkedin"],
)

# Career — application email
_prompts.add_version(
    "career.app_email",
    """Write a professional application email.
First line must be 'Subject: [subject line]'.
Rest is the email body.

Company: $company
Job Title: $job_title
Email Type: $email_type (cold, referral, follow_up)
Candidate Profile: $candidate_profile
Job Description: $job_description""",
    description="Draft application emails",
    tags=["career", "email"],
)

# Career — interview story bank
_prompts.add_version(
    "career.story_bank",
    """Based on this candidate profile and job, generate 4 STAR (Situation-Task-Action-Result) stories.
Return ONLY valid JSON. Key: stories (list of {title, situation, task, action, result, reflection, applicable_scenarios}).

Candidate: $candidate_profile
Job Title: $job_title
Company: $company""",
    description="Generate STAR interview story bank",
    tags=["career", "interview", "stories", "json"],
)

# Career — scam/ghost job detection
_prompts.add_version(
    "career.scam_check",
    """Evaluate this job posting for legitimacy. Return ONLY valid JSON.
Keys: risk_score (0.0-1.0, higher = more likely scam),
red_flags (list of warning signs),
legitimacy_indicators (positive signals),
verdict (LEGITIMATE, SUSPICIOUS, or SCAM),
recommendation (one sentence).

Job Title: $job_title
Company: $company
Description: $description""",
    description="Detect scam and ghost job postings",
    tags=["career", "safety", "json"],
)

# Career — negotiation scripts
_prompts.add_version(
    "career.negotiation",
    """Create a salary negotiation strategy. Return ONLY valid JSON.
Keys: talking_points (list of key arguments),
scripts (list of {scenario, what_to_say, expected_response, counter}),
market_data_tips (where to find comp data),
leverage_angles (ways to strengthen your position).

Role: $job_title
Company: $company
Skills: $skills
Target Salary: $target_salary""",
    description="Generate salary negotiation scripts",
    tags=["career", "negotiation", "json"],
)


# Career — archetype detection
_prompts.add_version(
    "career.archetype",
    """Classify this job into a primary archetype. Return ONLY valid JSON.
Keys: archetype (one of: LLMOps, Agentic_AI, Product_Manager, Solutions_Architect,
Frontend_Engineer, Data_Engineer, Platform_Engineer, ML_Engineer, DevOps,
Security, Full_Stack, Mobile, QA, Management, Transformation, Other),
confidence (0.0-1.0), sub_archetype, reasoning (one sentence).

Job Title: $job_title
Company: $company
Description: $description
Skills: $skills""",
    description="Classify job into archetype category",
    tags=["career", "classification", "json"],
)

# Career — full A-F evaluation report
_prompts.add_version(
    "career.full_eval",
    """Evaluate this job against the candidate CV. Return ONLY valid JSON.
Keys:
- overall_score: 1.0-5.0
- block_a (Role Match): {score, summary, strengths, gaps}
- block_b (CV Alignment): {score, matching_experience, missing_experience, recommendations}
- block_c (Level Strategy): {score, current_level, target_level, promotion_path, timeline}
- block_d (Comp Research): {score, market_range, suggested_range, negotiation_levers}
- block_e (Personalization): {score, resume_adaptations, cover_letter_angles, interview_emphasis}
- block_f (Interview Prep): {score, technical_areas, behavioral_stories, questions_to_prepare}
- verdict: STRONG_MATCH / GOOD_FIT / REACH / SKIP
- recommendation: one paragraph

Job Title: $job_title | Company: $company | Location: $location
Description: $description | Skills: $skills
CV: $cv_text
Candidate Profile: $candidate_profile""",
    description="Full 6-block A-F evaluation report",
    tags=["career", "evaluation", "json"],
)


# Startup — personalized cold email
_prompts.add_version(
    "startup.cold_email",
    """Write a personalized cold email to this startup.
Return ONLY valid JSON with keys "subject" and "body".

The email must:
- Be genuinely specific to this company (mention their industry and what they do)
- Reference their city/tech hub context
- Show the candidate's enthusiasm for their space (fintech, e-commerce, AI/ML, etc.)
- Be professional and concise (3-4 short paragraphs)
- Include the candidate's skills naturally, not as a list
- End with a call to action (call to discuss)

Company: $company_name
Industry: $industry
City: $city
Company Size: $size
Role: $role
Remote: $remote
Candidate Profile: $candidate_profile""",
    description="Personalized cold email to a startup company",
    tags=["startup", "email", "json"],
)


# IT Company — problem-solution cold email
_prompts.add_version(
    "it_company.cold_email",
    """Write a problem-solution cold email to this IT services/product company.
Return ONLY valid JSON with keys "subject" and "body".

The email must identify a likely business problem this type of company faces
and present the candidate as the solution. Use a professional, confident tone.

Problem-solution framing by company tier:
- Staff Augmentation / Software House: "Finding reliable developers who work US/EU timezones is hard. I'm a Pakistan-based developer comfortable with async workflows and client communication."
- Product Company: "Shipping features fast while managing tech debt is a constant challenge. I bring full-stack skills to help you ship and maintain quality."
- BPO / Outsourcing: "Maintaining consistent quality across client projects at scale requires disciplined engineers. I have experience delivering reliable code in team settings."
- IT Services / Consulting: "Scaling delivery teams for digital transformation projects needs adaptable developers. I can hit the ground running with modern stacks."

Company: $company_name
Services: $services
Company Size: $size
City: $city
Company Tier: $company_tier
Target Role: $role
Remote: $remote
Candidate Profile: $candidate_profile""",
    description="Problem-solution cold email to an IT company",
    tags=["it_company", "email", "json"],
)


def get_prompt_registry() -> PromptRegistry:
    return _prompts
