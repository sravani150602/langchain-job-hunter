"""
Adzuna Jobs API - covers Google, Amazon, Meta, Apple, Microsoft and more.
Free tier: 250 requests/month. Sign up at https://developer.adzuna.com/
"""
import httpx
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from ..models import Job
from ..config import settings
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/{page}"

PRIORITY_COMPANIES = {
    "google", "meta", "amazon", "apple", "microsoft", "nvidia",
    "paypal", "uber", "netflix", "stripe", "airbnb", "salesforce"
}


def is_priority(company: str) -> bool:
    return any(p in company.lower() for p in PRIORITY_COMPANIES)


def is_remote(location: str) -> bool:
    return "remote" in location.lower()


def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None


async def search_jobs(
    client: httpx.AsyncClient,
    what: str,
    company: Optional[str] = None,
    page: int = 1,
    results_per_page: int = 20
) -> List[Job]:
    if not settings.adzuna_app_id or not settings.adzuna_api_key:
        logger.warning("Adzuna API credentials not configured. Skipping Adzuna search.")
        return []

    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_api_key,
        "results_per_page": results_per_page,
        "what": what,
        "content-type": "application/json",
        "sort_by": "date",  # newest first
        "max_days_old": 7,
    }

    if company:
        params["company"] = company

    url = BASE_URL.format(page=page)

    try:
        resp = await client.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Adzuna search '{what}': HTTP {resp.status_code} - {resp.text[:200]}")
            return []

        data = resp.json()
        results = data.get("results", [])

        jobs = []
        for j in results:
            title = j.get("title", "")
            company_name = j.get("company", {}).get("display_name", "Unknown")
            location_data = j.get("location", {})
            location = location_data.get("display_name", "Not specified")

            posted_at = parse_date(j.get("created"))

            # Skip old jobs
            if posted_at:
                age_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
                if age_hours > 168:
                    continue

            description = j.get("description", "")
            salary_min = j.get("salary_min")
            salary_max = j.get("salary_max")

            job_type = "data-engineering" if "data engineer" in title.lower() else "software-engineering"

            jobs.append(Job(
                id=f"az_{j.get('id', '')}",
                title=title,
                company=company_name,
                location=location,
                posted_at=posted_at,
                url=j.get("redirect_url", ""),
                description=description[:3000],
                requirements=[],
                source="adzuna",
                applicant_count=None,
                job_type=job_type,
                is_priority=is_priority(company_name),
                remote=is_remote(location) or is_remote(description),
                salary_min=int(salary_min) if salary_min else None,
                salary_max=int(salary_max) if salary_max else None,
            ))

        return jobs

    except Exception as e:
        logger.error(f"Adzuna search error for '{what}': {e}")
        return []


async def fetch_faang_jobs(target_roles: List[str], faang_companies: List[str]) -> List[Job]:
    """Search Adzuna for FAANG company jobs matching target roles."""
    if not settings.adzuna_app_id or not settings.adzuna_api_key:
        return []

    async with httpx.AsyncClient() as client:
        tasks = []

        # Search for each role at FAANG companies
        for company in faang_companies[:10]:  # limit to top 10 to save API quota
            query = "software engineer OR data engineer new grad entry level"
            tasks.append(search_jobs(client, query, company=company, results_per_page=10))

        # Also do broad searches
        for role in ["new grad software engineer", "entry level data engineer"]:
            tasks.append(search_jobs(client, role, results_per_page=20))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs = []
    seen_ids = set()
    for result in results:
        if isinstance(result, list):
            for job in result:
                if job.id not in seen_ids:
                    seen_ids.add(job.id)
                    all_jobs.append(job)

    return all_jobs
