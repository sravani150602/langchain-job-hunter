"""
LangChain chain for generating personalized interview preparation questions.
Produces behavioral, technical, and company-specific questions.
"""
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..models import ParsedResume, InterviewPrep, InterviewQuestion
from ..config import settings

logger = logging.getLogger(__name__)

INTERVIEW_PROMPT = ChatPromptTemplate.from_template("""
You are a senior engineering interviewer helping a student prepare for a job interview.

## Target Job
Title: {job_title}
Company: {company}
Description: {job_description}
Requirements: {requirements}

## Candidate Profile
Skills: {skills}
Experience: {experience_summary}
Education: {education}

## Task
Generate targeted interview questions. Respond with ONLY valid JSON:
{{
  "behavioral": [
    {{
      "question": "Tell me about a time when...",
      "category": "behavioral",
      "hint": "Focus on: situation, task, action, result (STAR method)"
    }}
  ],
  "technical": [
    {{
      "question": "How would you design...",
      "category": "technical",
      "hint": "Key concepts to mention"
    }}
  ],
  "company_specific": [
    {{
      "question": "Why {company}?",
      "category": "company",
      "hint": "Research tip or talking point"
    }}
  ],
  "topics_to_study": ["topic1", "topic2", ...]
}}

Requirements:
- 4 behavioral questions (communication, teamwork, problem-solving, leadership)
- 5 technical questions based on the JD requirements and candidate skills
- 3 company-specific questions
- 5-8 topics to study before the interview
- hints should be genuinely helpful preparation tips
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


async def generate_interview_prep(
    resume: ParsedResume,
    job_id: str,
    job_title: str,
    company: str,
    job_description: str,
    requirements: list[str],
) -> InterviewPrep:
    """Generate personalized interview questions using LangChain."""
    llm = get_llm()

    exp_summary = "; ".join([
        f"{e.title} at {e.company} ({e.duration})" for e in resume.experience
    ]) or "Student / Fresh Graduate"

    edu_summary = "; ".join([
        f"{e.degree} from {e.institution} ({e.year})" for e in resume.education
    ]) or resume.target_role or "Computer Science Student"

    if not llm:
        return _fallback_prep(job_id, job_title, company)

    parser = JsonOutputParser()
    chain = INTERVIEW_PROMPT | llm | parser

    try:
        result = await chain.ainvoke({
            "job_title": job_title,
            "company": company,
            "job_description": job_description[:2000],
            "requirements": "; ".join(requirements[:8]),
            "skills": ", ".join(resume.skills[:15]),
            "experience_summary": exp_summary,
            "education": edu_summary,
        })

        def parse_questions(items):
            out = []
            for item in (items or []):
                try:
                    out.append(InterviewQuestion(**item))
                except Exception:
                    pass
            return out

        return InterviewPrep(
            job_id=job_id,
            job_title=job_title,
            company=company,
            behavioral=parse_questions(result.get("behavioral", [])),
            technical=parse_questions(result.get("technical", [])),
            company_specific=parse_questions(result.get("company_specific", [])),
            topics_to_study=result.get("topics_to_study", []),
        )
    except Exception as e:
        logger.error(f"Interview prep error: {e}")
        return _fallback_prep(job_id, job_title, company)


def _fallback_prep(job_id: str, job_title: str, company: str) -> InterviewPrep:
    return InterviewPrep(
        job_id=job_id,
        job_title=job_title,
        company=company,
        behavioral=[
            InterviewQuestion(
                question="Tell me about a challenging project you worked on.",
                category="behavioral",
                hint="Use the STAR method: Situation, Task, Action, Result",
            ),
            InterviewQuestion(
                question="Describe a time you had to learn a new technology quickly.",
                category="behavioral",
                hint="Show adaptability and self-learning ability",
            ),
        ],
        technical=[
            InterviewQuestion(
                question=f"How would you design a scalable backend for {job_title.lower()} tasks?",
                category="technical",
                hint="Discuss trade-offs, databases, caching, and APIs",
            ),
        ],
        company_specific=[
            InterviewQuestion(
                question=f"Why do you want to work at {company}?",
                category="company",
                hint=f"Research {company}'s products, culture, and recent news",
            ),
        ],
        topics_to_study=["Data Structures & Algorithms", "System Design", "SQL", "REST APIs"],
    )
