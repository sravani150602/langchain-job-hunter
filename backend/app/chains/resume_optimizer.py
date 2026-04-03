"""
LangChain chain for optimizing resume content for a specific job.
Rewrites bullet points, highlights keywords, and suggests improvements.
"""
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..models import ParsedResume, ResumeOptimization, OptimizedBullet
from ..config import settings

logger = logging.getLogger(__name__)

OPTIMIZE_PROMPT = ChatPromptTemplate.from_template("""
You are an expert resume coach helping a student optimize their resume for a specific job.

## Target Job
Title: {job_title}
Company: {company}
Description: {job_description}
Requirements: {requirements}

## Current Resume
Skills: {skills}
Experience Bullets:
{experience_bullets}

## Task
Optimize this resume for the target job. Respond with ONLY valid JSON:
{{
  "keywords_to_add": ["keyword1", "keyword2", ...],
  "skills_to_highlight": ["skill1", "skill2", ...],
  "summary_rewrite": "A tailored 2-3 sentence professional summary for this specific role",
  "optimized_bullets": [
    {{
      "original": "original bullet point",
      "improved": "improved version with stronger action verbs, metrics, and job-relevant keywords",
      "reason": "why this change helps"
    }}
  ]
}}

Rules:
- Use strong action verbs (Engineered, Architected, Reduced, Increased, etc.)
- Add measurable impact where possible (%, x faster, N users, etc.)
- Include keywords from the job description naturally
- Keep bullets concise (1-2 lines)
- Provide optimized_bullets for up to 5 most impactful bullets
- keywords_to_add should be skills/tools from the JD that the candidate should mention
""")


def get_llm():
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=2048,
        )
    elif settings.openai_api_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            max_tokens=2048,
        )
    return None


async def optimize_resume(
    resume: ParsedResume,
    job_id: str,
    job_title: str,
    company: str,
    job_description: str,
    requirements: list[str],
) -> ResumeOptimization:
    """Generate AI resume optimization suggestions for a target job."""
    llm = get_llm()

    # Flatten experience bullets for the prompt
    bullets = []
    for exp in resume.experience:
        for b in exp.bullets:
            bullets.append(f"[{exp.title} @ {exp.company}] {b}")
    # Also include project descriptions
    for proj in resume.projects:
        if proj.description:
            bullets.append(f"[Project: {proj.name}] {proj.description}")

    if not llm:
        return ResumeOptimization(
            job_id=job_id,
            job_title=job_title,
            company=company,
            keywords_to_add=requirements[:5],
            skills_to_highlight=resume.skills[:5],
            summary_rewrite=f"Motivated {resume.target_role or 'Software Engineer'} seeking a role at {company}.",
            optimized_bullets=[],
        )

    parser = JsonOutputParser()
    chain = OPTIMIZE_PROMPT | llm | parser

    try:
        result = await chain.ainvoke({
            "job_title": job_title,
            "company": company,
            "job_description": job_description[:2000],
            "requirements": "; ".join(requirements[:8]),
            "skills": ", ".join(resume.skills),
            "experience_bullets": "\n".join(bullets[:10]),
        })

        optimized_bullets = [
            OptimizedBullet(**b) for b in result.get("optimized_bullets", [])
        ]
        return ResumeOptimization(
            job_id=job_id,
            job_title=job_title,
            company=company,
            keywords_to_add=result.get("keywords_to_add", []),
            skills_to_highlight=result.get("skills_to_highlight", []),
            summary_rewrite=result.get("summary_rewrite", ""),
            optimized_bullets=optimized_bullets,
        )
    except Exception as e:
        logger.error(f"Resume optimization error: {e}")
        return ResumeOptimization(
            job_id=job_id,
            job_title=job_title,
            company=company,
            keywords_to_add=requirements[:5],
            skills_to_highlight=resume.skills[:5],
            summary_rewrite="",
            optimized_bullets=[],
        )
