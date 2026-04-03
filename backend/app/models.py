from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime, timezone


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    posted_at: Optional[datetime] = None
    url: str
    description: str = ""
    requirements: List[str] = []
    source: str  # greenhouse / lever / adzuna / amazon
    applicant_count: Optional[int] = None  # only where available
    match_score: Optional[int] = None  # 0-100, from LangChain
    match_reasons: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    job_summary: Optional[str] = None
    job_type: str = "software-engineering"  # software-engineering / data-engineering
    is_priority: bool = False  # FAANG or target companies
    remote: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "USD"

    @computed_field
    @property
    def hours_ago(self) -> Optional[float]:
        if self.posted_at is None:
            return None
        now = datetime.now(timezone.utc)
        posted = self.posted_at
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        delta = now - posted
        return round(delta.total_seconds() / 3600, 1)

    @computed_field
    @property
    def posted_label(self) -> str:
        h = self.hours_ago
        if h is None:
            return "Unknown"
        if h < 1:
            return f"{int(h * 60)}m ago"
        if h < 24:
            return f"{int(h)}h ago"
        days = int(h / 24)
        return f"{days}d ago"


class UserProfile(BaseModel):
    skills: List[str] = Field(
        default=["Python", "Java", "SQL", "AWS", "Docker", "React", "LangChain"],
        description="List of technical skills"
    )
    yoe: float = Field(default=0, description="Years of experience (0 for new grad)")
    education: str = Field(default="BS Computer Science", description="Highest education")
    preferred_roles: List[str] = Field(
        default=["Software Engineer", "Data Engineer"],
        description="Preferred job titles"
    )
    preferred_locations: List[str] = Field(
        default=["Remote", "San Francisco", "New York", "Seattle"],
        description="Preferred work locations"
    )
    remote_only: bool = False
    resume_summary: str = Field(
        default="",
        description="Brief summary of experience/background"
    )


class JobSearchRequest(BaseModel):
    profile: UserProfile
    companies: Optional[List[str]] = None  # filter by company names
    roles: Optional[List[str]] = None
    max_hours_ago: int = 48  # only show jobs posted within N hours
    limit: int = 50


class RefreshResponse(BaseModel):
    jobs_fetched: int
    sources: dict
    duration_seconds: float
    timestamp: datetime


# ── Resume models ──────────────────────────────────────────
class ResumeEducation(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""
    gpa: str = ""


class ResumeExperience(BaseModel):
    title: str = ""
    company: str = ""
    duration: str = ""
    bullets: List[str] = []


class ResumeProject(BaseModel):
    name: str = ""
    description: str = ""
    technologies: List[str] = []


class ParsedResume(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: List[str] = []
    education: List[ResumeEducation] = []
    experience: List[ResumeExperience] = []
    projects: List[ResumeProject] = []
    target_role: str = ""
    summary: str = ""
    raw_text: str = ""


# ── Job detail analysis ────────────────────────────────────
class JobAnalysis(BaseModel):
    job_id: str
    score: int
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    strengths: List[str] = []
    recommendations: List[str] = []
    verdict: str = ""  # apply-now | consider | skip


# ── Resume optimization ────────────────────────────────────
class OptimizedBullet(BaseModel):
    original: str
    improved: str
    reason: str


class ResumeOptimization(BaseModel):
    job_id: str
    job_title: str
    company: str
    keywords_to_add: List[str] = []
    optimized_bullets: List[OptimizedBullet] = []
    skills_to_highlight: List[str] = []
    summary_rewrite: str = ""


# ── Interview prep ─────────────────────────────────────────
class InterviewQuestion(BaseModel):
    question: str
    category: str  # behavioral | technical | company
    hint: str = ""


class InterviewPrep(BaseModel):
    job_id: str
    job_title: str
    company: str
    behavioral: List[InterviewQuestion] = []
    technical: List[InterviewQuestion] = []
    company_specific: List[InterviewQuestion] = []
    topics_to_study: List[str] = []


# ── Application tracker ─────────────────────────────────────
class TrackerStatus(str):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"


class TrackerEntry(BaseModel):
    id: str
    job_id: str
    job_title: str
    company: str
    location: str = ""
    url: str = ""
    status: str = "saved"  # saved | applied | interviewing | offer | rejected
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TrackerUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
