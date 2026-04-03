"""
LangChain chain for parsing resume text into structured JSON.
Uses LCEL (LangChain Expression Language) with a JSON output parser.
"""
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..models import ParsedResume
from ..config import settings

logger = logging.getLogger(__name__)

PARSE_PROMPT = ChatPromptTemplate.from_template("""
You are an expert resume parser. Extract structured information from the resume text below.

Resume Text:
---
{resume_text}
---

Extract the following fields and respond with ONLY valid JSON:
{{
  "name": "full name",
  "email": "email address or empty string",
  "phone": "phone number or empty string",
  "target_role": "inferred target job role (e.g. Software Engineer, Data Engineer)",
  "summary": "2-3 sentence professional summary",
  "skills": ["skill1", "skill2", ...],
  "education": [
    {{
      "degree": "degree name",
      "institution": "university name",
      "year": "graduation year or range",
      "gpa": "GPA if listed else empty string"
    }}
  ],
  "experience": [
    {{
      "title": "job title",
      "company": "company name",
      "duration": "date range",
      "bullets": ["bullet point 1", "bullet point 2"]
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "description": "brief description",
      "technologies": ["tech1", "tech2"]
    }}
  ]
}}

Rules:
- skills should include ALL technical skills, tools, languages, frameworks mentioned
- If a field is not found, use empty string or empty list
- For fresh students, internships and course projects count as experience/projects
- Keep bullet points concise but informative
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


def _smart_fallback_parse(resume_text: str) -> ParsedResume:
    """
    Regex-based resume parser used when LLM is unavailable or fails.
    Extracts name, email, phone, and skills from raw text.
    """
    import re

    lines = [l.strip() for l in resume_text.strip().splitlines() if l.strip()]

    # --- Name: usually the first non-empty line that looks like a name ---
    name = ""
    for line in lines[:5]:
        # A name line: 2-4 words, mostly letters, no @ or digits
        if re.match(r'^[A-Za-z][A-Za-z\s\-\.]{3,40}$', line) and '@' not in line:
            name = line.strip()
            break

    # --- Email ---
    email_match = re.search(r'[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}', resume_text, re.I)
    email = email_match.group(0) if email_match else ""

    # --- Phone ---
    phone_match = re.search(r'(\+?1?\s?)?(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})', resume_text)
    phone = phone_match.group(0).strip() if phone_match else ""

    # --- Skills keyword scan ---
    common_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Swift", "Kotlin",
        "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Cassandra",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Linux",
        "React", "Angular", "Vue", "Node.js", "FastAPI", "Django", "Flask", "Spring Boot",
        "Git", "REST", "GraphQL", "LangChain", "TensorFlow", "PyTorch",
        "Machine Learning", "Deep Learning", "NLP", "Data Engineering",
        "Spark", "Kafka", "Airflow", "dbt", "Snowflake", "Databricks",
        "Pandas", "NumPy", "Scikit-learn", "Jupyter",
    ]
    found_skills = [s for s in common_skills if s.lower() in resume_text.lower()]

    # --- Education: look for degree keywords ---
    education = []
    edu_pattern = re.search(
        r'(B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?Eng|Bachelor|Master|PhD)[^\n]{0,80}(Computer|Software|Data|Engineering|Science|Information)[^\n]{0,60}',
        resume_text, re.I
    )
    if edu_pattern:
        from ..models import ResumeEducation
        education = [ResumeEducation(degree=edu_pattern.group(0)[:80].strip())]

    # --- Target role guess ---
    target_role = "Software Engineer"
    if any(k in resume_text.lower() for k in ["data engineer", "data pipeline", "etl", "spark", "airflow"]):
        target_role = "Data Engineer"
    elif any(k in resume_text.lower() for k in ["machine learning", "ml engineer", "deep learning"]):
        target_role = "ML Engineer"

    summary = f"Resume parsed for {name or 'candidate'}. Found {len(found_skills)} skills."

    return ParsedResume(
        name=name,
        email=email,
        phone=phone,
        skills=found_skills,
        education=education,
        target_role=target_role,
        summary=summary,
        raw_text=resume_text,
    )


async def parse_resume(resume_text: str) -> ParsedResume:
    """Parse raw resume text into a structured ParsedResume using LangChain."""
    llm = get_llm()

    if not llm:
        logger.warning("No LLM configured — using smart regex fallback parser")
        return _smart_fallback_parse(resume_text)

    parser = JsonOutputParser(pydantic_object=ParsedResume)
    chain = PARSE_PROMPT | llm | parser

    try:
        result = await chain.ainvoke({"resume_text": resume_text[:6000]})
        result["raw_text"] = resume_text
        parsed = ParsedResume(**result)
        # If LLM returned empty name, use regex fallback for name/email
        if not parsed.name:
            fallback = _smart_fallback_parse(resume_text)
            parsed.name = fallback.name
            parsed.email = parsed.email or fallback.email
            parsed.phone = parsed.phone or fallback.phone
        return parsed
    except Exception as e:
        logger.error(f"Resume LLM parse error: {e} — falling back to regex parser")
        return _smart_fallback_parse(resume_text)
