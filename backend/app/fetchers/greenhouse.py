"""
Greenhouse Boards API - completely public, no auth needed.
Many top companies post on Greenhouse: Uber, Stripe, Airbnb, Discord, etc.
"""
import httpx
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from ..models import Job
import re
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://api.greenhouse.io/v1/boards/{company}/jobs"
JOB_URL = "https://api.greenhouse.io/v1/boards/{company}/jobs/{job_id}"

# Mapping of company slugs to display names
COMPANY_DISPLAY_NAMES = {
    "uber": "Uber",
    "airbnb": "Airbnb",
    "stripe": "Stripe",
    "discord": "Discord",
    "figma": "Figma",
    "databricks": "Databricks",
    "snowflake": "Snowflake",
    "coinbase": "Coinbase",
    "robinhood": "Robinhood",
    "lyft": "Lyft",
    "doordash": "DoorDash",
    "instacart": "Instacart",
    "brex": "Brex",
    "plaid": "Plaid",
    "scale": "Scale AI",
    "anthropic": "Anthropic",
    "openai": "OpenAI",
}

PRIORITY_COMPANIES = {"uber", "airbnb", "stripe", "databricks", "snowflake", "openai", "anthropic"}

# Keywords to identify relevant roles
ROLE_KEYWORDS = [
    "software engineer", "software developer", "data engineer",
    "backend engineer", "frontend engineer", "full stack",
    "machine learning engineer", "ml engineer", "site reliability",
    "sre", "platform engineer", "new grad", "university grad",
    "entry level", "junior", "associate engineer"
]

DATA_KEYWORDS = ["data engineer", "data platform", "data infrastructure", "analytics engineer"]


def is_relevant_role(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in ROLE_KEYWORDS)


def is_data_role(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in DATA_KEYWORDS)


def is_remote(location: str) -> bool:
    return "remote" in location.lower()


def extract_requirements(description: str) -> List[str]:
    """Pull bullet points that look like requirements from HTML description."""
    text = re.sub(r'<[^>]+>', ' ', description)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    requirements = []
    capture = False
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in ["requirements", "qualifications", "what you bring", "what we're looking for", "you have"]):
            capture = True
            continue
        if capture:
            if len(line) > 10 and len(line) < 200:
                requirements.append(line.lstrip('•-* '))
            if len(requirements) >= 8:
                break
    return requirements[:8]


async def fetch_company_jobs(client: httpx.AsyncClient, company: str, target_roles: List[str]) -> List[Job]:
    url = BASE_URL.format(company=company)
    try:
        resp = await client.get(url, params={"content": "true"}, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Greenhouse {company}: HTTP {resp.status_code}")
            return []

        data = resp.json()
        jobs_data = data.get("jobs", [])
        display_name = COMPANY_DISPLAY_NAMES.get(company, company.title())
        is_priority = company in PRIORITY_COMPANIES

        jobs = []
        for j in jobs_data:
            title = j.get("title", "")
            if not is_relevant_role(title):
                continue

            # Parse location
            dept = j.get("departments", [{}])
            location_data = j.get("location", {})
            location = location_data.get("name", "Not specified") if isinstance(location_data, dict) else str(location_data)

            # Parse posted date
            posted_at = None
            updated_at = j.get("updated_at") or j.get("created_at")
            if updated_at:
                try:
                    posted_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                except Exception:
                    pass

            # Skip jobs older than 7 days to keep data fresh
            if posted_at:
                age_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
                if age_hours > 168:  # 7 days
                    continue

            description = j.get("content", "")
            requirements = extract_requirements(description)

            job_type = "data-engineering" if is_data_role(title) else "software-engineering"

            jobs.append(Job(
                id=f"gh_{company}_{j['id']}",
                title=title,
                company=display_name,
                location=location,
                posted_at=posted_at,
                url=j.get("absolute_url", f"https://boards.greenhouse.io/{company}"),
                description=description[:3000],
                requirements=requirements,
                source="greenhouse",
                applicant_count=None,  # Greenhouse doesn't expose this via API
                job_type=job_type,
                is_priority=is_priority,
                remote=is_remote(location),
            ))

        return jobs

    except Exception as e:
        logger.error(f"Greenhouse fetch error for {company}: {e}")
        return []


async def fetch_all_greenhouse_jobs(companies: List[str], target_roles: List[str]) -> List[Job]:
    async with httpx.AsyncClient(headers={"User-Agent": "JobHunterBot/1.0"}) as client:
        tasks = [fetch_company_jobs(client, company, target_roles) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs = []
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)

    return all_jobs
