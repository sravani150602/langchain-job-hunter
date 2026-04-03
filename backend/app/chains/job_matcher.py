"""
LangChain-powered job matching engine.
Scores each job against the user's profile and explains why it's a good/bad fit.

LangChain components used:
  - LCEL (LangChain Expression Language): ChatPromptTemplate | LLM | JsonOutputParser
  - LangSmith: automatic tracing of every chain run (set LANGCHAIN_API_KEY to enable)
  - ChatAnthropic / ChatOpenAI: LLM providers
"""
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.tracers.context import tracing_v2_enabled
from pydantic import BaseModel, Field
from typing import List, Optional
import asyncio
import logging

from ..models import Job, UserProfile
from ..config import settings

logger = logging.getLogger(__name__)

# Activate LangSmith tracing if API key is present
if settings.langchain_api_key:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)
    logger.info(f"LangSmith tracing enabled → project: {settings.langchain_project}")


def get_llm():
    """Get LLM based on configured provider."""
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-haiku-4-5-20251001",  # Haiku for speed + cost
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=512,
        )
    elif settings.openai_api_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",  # Cheap and fast
            openai_api_key=settings.openai_api_key,
            max_tokens=512,
        )
    else:
        logger.warning("No LLM API key configured. Job matching will use keyword scoring only.")
        return None


class JobMatchResult(BaseModel):
    score: int = Field(description="Match score from 0 to 100")
    reasons: List[str] = Field(description="Top 3 reasons this job matches your profile")
    missing_skills: List[str] = Field(description="Skills you might be lacking (max 3)")
    summary: str = Field(description="One-sentence job summary for quick reading")
    apply_urgency: str = Field(description="One of: apply-now, consider, skip")


MATCH_PROMPT = ChatPromptTemplate.from_template("""
You are a career advisor helping a job seeker evaluate job opportunities.
Analyze how well this job matches the candidate profile and respond in the exact JSON format specified.

## Candidate Profile
- Skills: {skills}
- Years of Experience: {yoe} (0 = new grad / fresh graduate)
- Education: {education}
- Preferred Roles: {preferred_roles}
- Resume Summary: {resume_summary}

## Job Posting
- Title: {title}
- Company: {company}
- Location: {location}
- Description: {description}
- Requirements: {requirements}

## Instructions
Score the match from 0-100 where:
- 80-100: Excellent match, apply immediately
- 60-79: Good match, worth applying
- 40-59: Partial match, stretch role
- 0-39: Poor match, skip

Be encouraging but realistic. For new grads (YOE=0), internships count and projects count.
Focus on whether the role fits the candidate's trajectory, not just years of experience.

Respond with ONLY valid JSON matching this schema:
{{
  "score": <integer 0-100>,
  "reasons": ["reason1", "reason2", "reason3"],
  "missing_skills": ["skill1", "skill2"],
  "summary": "one sentence summary of what this role does",
  "apply_urgency": "apply-now|consider|skip"
}}
""")


def keyword_score(job: Job, profile: UserProfile) -> int:
    """Fallback scoring when no LLM is available."""
    score = 0
    text = (job.title + " " + job.description + " " + " ".join(job.requirements)).lower()

    # Skills match
    skills_found = sum(1 for skill in profile.skills if skill.lower() in text)
    score += min(50, skills_found * 10)

    # Role match
    role_match = any(role.lower() in job.title.lower() for role in profile.preferred_roles)
    if role_match:
        score += 20

    # Priority company bonus
    if job.is_priority:
        score += 10

    # Recent posting bonus
    if job.hours_ago and job.hours_ago < 24:
        score += 10

    # Remote preference
    if profile.remote_only and job.remote:
        score += 10

    return min(100, score)


async def match_job_with_llm(job: Job, profile: UserProfile, llm) -> dict:
    """Use LangChain to intelligently score a job."""
    parser = JsonOutputParser(pydantic_object=JobMatchResult)
    chain = MATCH_PROMPT | llm | parser

    try:
        result = await chain.ainvoke({
            "skills": ", ".join(profile.skills),
            "yoe": profile.yoe,
            "education": profile.education,
            "preferred_roles": ", ".join(profile.preferred_roles),
            "resume_summary": profile.resume_summary or "Fresh graduate looking for software/data engineering roles",
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description[:1500],  # truncate to save tokens
            "requirements": "; ".join(job.requirements[:5]),
        })
        return result
    except Exception as e:
        logger.error(f"LLM match error for {job.title} at {job.company}: {e}")
        score = keyword_score(job, profile)
        return {
            "score": score,
            "reasons": [f"Matched based on your skills: {', '.join(profile.skills[:3])}"],
            "missing_skills": [],
            "summary": job.title,
            "apply_urgency": "consider" if score >= 60 else "skip",
        }


async def score_jobs_batch(jobs: List[Job], profile: UserProfile, batch_size: int = 5) -> List[Job]:
    """Score a list of jobs against a user profile using LangChain."""
    llm = get_llm()

    if not llm:
        # Keyword-based fallback
        for job in jobs:
            score = keyword_score(job, profile)
            job.match_score = score
            job.match_reasons = [f"Based on skills: {', '.join(profile.skills[:3])}"]
            job.missing_skills = []
            job.job_summary = job.title
        return sorted(jobs, key=lambda j: j.match_score or 0, reverse=True)

    # Process in batches to avoid rate limits
    scored_jobs = []
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]

        async def score_one(job):
            result = await match_job_with_llm(job, profile, llm)
            job.match_score = result.get("score", 0)
            job.match_reasons = result.get("reasons", [])
            job.missing_skills = result.get("missing_skills", [])
            job.job_summary = result.get("summary", job.title)
            return job

        batch_results = await asyncio.gather(*[score_one(job) for job in batch])
        scored_jobs.extend(batch_results)

        # Small delay between batches to respect rate limits
        if i + batch_size < len(jobs):
            await asyncio.sleep(0.5)

    # Sort by score descending, priority companies first
    scored_jobs.sort(key=lambda j: (j.is_priority, j.match_score or 0), reverse=True)
    return scored_jobs
