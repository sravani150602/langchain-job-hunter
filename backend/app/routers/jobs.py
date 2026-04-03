import asyncio
import time
import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from ..models import Job, UserProfile, JobSearchRequest, RefreshResponse
from ..database import job_store
from ..config import settings
from ..fetchers.jobright import fetch_jobright_jobs
from ..fetchers.greenhouse import fetch_all_greenhouse_jobs
from ..fetchers.lever import fetch_all_lever_jobs
from ..chains.job_matcher import score_jobs_batch
import logging

# Enable LangSmith tracing if configured
if settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# Default profile used when no profile provided
DEFAULT_PROFILE = UserProfile(
    skills=["Python", "Java", "SQL", "AWS", "Docker", "React", "LangChain", "Git"],
    yoe=0,
    education="BS Computer Science",
    preferred_roles=["Software Engineer", "Data Engineer", "Backend Engineer"],
    preferred_locations=["Remote", "San Francisco", "New York", "Seattle"],
    resume_summary="Recent CS graduate with experience in Python, Java, and SQL. "
                   "Built projects using AWS, Docker, and React. Looking for SWE or data engineering roles."
)

_refresh_lock = asyncio.Lock()
_is_refreshing = False


async def _do_refresh(profile: UserProfile = None) -> RefreshResponse:
    """Fetch jobs from all sources and score them."""
    global _is_refreshing
    if _is_refreshing:
        raise HTTPException(status_code=409, detail="Refresh already in progress")

    async with _refresh_lock:
        _is_refreshing = True
        start = time.time()
        sources = {}

        try:
            profile = profile or DEFAULT_PROFILE
            logger.info("Starting job refresh from all sources...")

            # Fetch from all sources concurrently
            # jobright.ai is primary (covers new-grad SWE/DE roles from all major companies)
            # Greenhouse + Lever are kept as backup for company-direct postings
            jobright_task = fetch_jobright_jobs(max_jobs=settings.jobright_max_jobs)
            greenhouse_task = fetch_all_greenhouse_jobs(
                settings.greenhouse_companies, settings.target_roles
            )
            lever_task = fetch_all_lever_jobs(settings.lever_companies)

            results = await asyncio.gather(
                jobright_task, greenhouse_task, lever_task,
                return_exceptions=True
            )

            all_jobs: List[Job] = []
            source_names = ["jobright", "greenhouse", "lever"]

            for source, result in zip(source_names, results):
                if isinstance(result, list):
                    sources[source] = len(result)
                    all_jobs.extend(result)
                    logger.info(f"{source}: {len(result)} jobs")
                else:
                    sources[source] = 0
                    logger.error(f"{source} failed: {result}")

            # Deduplicate by URL
            seen_urls = set()
            unique_jobs = []
            for job in all_jobs:
                if job.url not in seen_urls:
                    seen_urls.add(job.url)
                    unique_jobs.append(job)

            logger.info(f"Total unique jobs before scoring: {len(unique_jobs)}")

            # Score with LangChain (only top candidates to save API calls)
            # Sort by recency first, score the freshest 100
            unique_jobs.sort(key=lambda j: j.hours_ago or 999)
            to_score = unique_jobs[:100]
            rest = unique_jobs[100:]

            scored = await score_jobs_batch(to_score, profile, batch_size=5)

            # Give rest a keyword score
            for job in rest:
                job.match_score = 30

            all_scored = scored + rest
            all_scored.sort(key=lambda j: (j.is_priority, j.match_score or 0), reverse=True)

            job_store.save_jobs(all_scored)
            duration = round(time.time() - start, 2)

            logger.info(f"Refresh complete: {len(all_scored)} jobs in {duration}s")
            return RefreshResponse(
                jobs_fetched=len(all_scored),
                sources=sources,
                duration_seconds=duration,
                timestamp=datetime.now(timezone.utc),
            )

        finally:
            _is_refreshing = False


@router.get("/", response_model=List[dict])
async def get_jobs(
    max_hours_ago: int = Query(48, description="Only show jobs posted within N hours"),
    job_type: Optional[str] = Query(None, description="software-engineering or data-engineering"),
    priority_only: bool = Query(False, description="Only FAANG and top companies"),
    remote_only: bool = Query(False, description="Only remote jobs"),
    min_score: int = Query(0, description="Minimum match score (0-100)"),
    limit: int = Query(50, le=200),
):
    """Get all cached jobs with optional filters."""
    jobs = job_store.get_jobs_filtered(
        max_hours_ago=max_hours_ago,
        job_type=job_type,
        priority_only=priority_only,
        remote_only=remote_only,
        min_score=min_score,
    )
    jobs = jobs[:limit]
    return [j.model_dump(mode="json") for j in jobs]


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_jobs(background_tasks: BackgroundTasks, profile: Optional[UserProfile] = None):
    """Trigger a fresh job fetch from all sources. Runs in background."""
    background_tasks.add_task(_do_refresh, profile)
    return RefreshResponse(
        jobs_fetched=0,
        sources={},
        duration_seconds=0,
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/refresh/sync", response_model=RefreshResponse)
async def refresh_jobs_sync(profile: Optional[UserProfile] = None):
    """Synchronously refresh jobs (waits for completion). Use for first load."""
    return await _do_refresh(profile)


@router.get("/status")
async def get_status():
    return {
        "total_jobs": job_store.total_count,
        "last_refresh": job_store.last_refresh.isoformat() if job_store.last_refresh else None,
        "is_refreshing": _is_refreshing,
        "sources_configured": {
            "jobright": True,      # Primary source — no key needed
            "greenhouse": True,    # Backup — no key needed
            "lever": True,         # Backup — no key needed
            "langsmith": bool(settings.langchain_api_key),  # Tracing
        }
    }


@router.post("/score", response_model=List[dict])
async def score_jobs_with_profile(request: JobSearchRequest):
    """Re-score all jobs against a custom profile."""
    jobs = job_store.get_jobs_filtered(max_hours_ago=request.max_hours_ago)

    if request.companies:
        companies_lower = [c.lower() for c in request.companies]
        jobs = [j for j in jobs if any(c in j.company.lower() for c in companies_lower)]

    jobs = jobs[:request.limit]
    scored = await score_jobs_batch(jobs, request.profile, batch_size=5)
    return [j.model_dump(mode="json") for j in scored]
