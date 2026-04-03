"""
Resume upload, parsing, per-job analysis, optimization, and interview prep endpoints.
"""
import io
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException

from ..models import ParsedResume, JobAnalysis, ResumeOptimization, InterviewPrep
from ..chains.resume_parser import parse_resume
from ..chains.resume_optimizer import optimize_resume
from ..chains.interview_prep import generate_interview_prep
from ..chains.job_matcher import match_job_with_llm, keyword_score, get_llm
from ..database import job_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["resume"])

# In-memory resume store (one resume per session for demo)
_current_resume: ParsedResume | None = None


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)


def _extract_text_from_docx(file_bytes: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


@router.post("/upload", response_model=ParsedResume)
async def upload_resume(file: UploadFile = File(...)):
    """Upload a PDF or DOCX resume and parse it with AI."""
    global _current_resume

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    filename = file.filename.lower()
    if not (filename.endswith(".pdf") or filename.endswith(".docx") or filename.endswith(".doc")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    # Extract text
    try:
        if filename.endswith(".pdf"):
            raw_text = _extract_text_from_pdf(file_bytes)
        else:
            raw_text = _extract_text_from_docx(file_bytes)
    except Exception as e:
        logger.error(f"File extraction error: {e}")
        raise HTTPException(status_code=422, detail=f"Could not read file: {str(e)}")

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="No text found in resume. Try a different file.")

    # Parse with LangChain
    parsed = await parse_resume(raw_text)
    _current_resume = parsed
    logger.info(f"Resume parsed: {parsed.name}, {len(parsed.skills)} skills")
    return parsed


@router.get("/", response_model=ParsedResume | None)
async def get_resume():
    """Get the currently uploaded resume."""
    return _current_resume


@router.get("/analyze/{job_id}", response_model=JobAnalysis)
async def analyze_job_fit(job_id: str):
    """Analyze how well the current resume matches a specific job."""
    if _current_resume is None:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")

    job = job_store._jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from ..models import UserProfile
    profile = UserProfile(
        skills=_current_resume.skills,
        yoe=0,
        education=_current_resume.education[0].degree if _current_resume.education else "BS Computer Science",
        preferred_roles=[_current_resume.target_role] if _current_resume.target_role else ["Software Engineer"],
        resume_summary=_current_resume.summary,
    )

    llm = get_llm()
    if llm:
        result = await match_job_with_llm(job, profile, llm)
    else:
        score = keyword_score(job, profile)
        result = {
            "score": score,
            "reasons": [f"Matched {len(_current_resume.skills)} skills"],
            "missing_skills": [],
            "summary": job.title,
            "apply_urgency": "consider" if score >= 60 else "skip",
        }

    # Skill matching details
    job_text = (job.description + " " + " ".join(job.requirements)).lower()
    matched = [s for s in _current_resume.skills if s.lower() in job_text]
    missing = result.get("missing_skills", [])

    return JobAnalysis(
        job_id=job_id,
        score=result.get("score", 0),
        matched_skills=matched,
        missing_skills=missing,
        strengths=result.get("reasons", []),
        recommendations=[f"Add '{s}' to your resume" for s in missing[:3]],
        verdict=result.get("apply_urgency", "consider"),
    )


@router.get("/optimize/{job_id}", response_model=ResumeOptimization)
async def optimize_for_job(job_id: str):
    """Get AI resume optimization suggestions for a specific job."""
    if _current_resume is None:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")

    job = job_store._jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return await optimize_resume(
        resume=_current_resume,
        job_id=job_id,
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        requirements=job.requirements,
    )


@router.get("/interview/{job_id}", response_model=InterviewPrep)
async def get_interview_prep(job_id: str):
    """Generate interview preparation questions for a specific job."""
    if _current_resume is None:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")

    job = job_store._jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return await generate_interview_prep(
        resume=_current_resume,
        job_id=job_id,
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        requirements=job.requirements,
    )
