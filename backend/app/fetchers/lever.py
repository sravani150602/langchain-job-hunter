"""
Lever Postings API - public, no auth needed.
Companies like Netflix, Reddit, Dropbox use Lever.
"""
import httpx
import asyncio
from datetime import datetime, timezone
from typing import List
from ..models import Job
import re
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://api.lever.co/v0/postings/{company}"

COMPANY_DISPLAY_NAMES = {
    "netflix": "Netflix",
    "reddit": "Reddit",
    "dropbox": "Dropbox",
    "zendesk": "Zendesk",
}

PRIORITY_COMPANIES = {"netflix"}

ROLE_KEYWORDS = [
    "software engineer", "software developer", "data engineer",
    "backend engineer", "frontend engineer", "full stack",
    "machine learning engineer", "ml engineer", "site reliability",
    "sre", "platform engineer", "new grad", "university grad",
    "entry level", "junior", "associate engineer"
]

DATA_KEYWORDS = ["data engineer", "data platform", "data infrastructure", "analytics engineer"]


def is_relevant_role(title: str) -> bool:
    return any(kw in title.lower() for kw in ROLE_KEYWORDS)


def is_data_role(title: str) -> bool:
    return any(kw in title.lower() for kw in DATA_KEYWORDS)


def is_remote(location: str) -> bool:
    return "remote" in location.lower()


def extract_requirements_from_lever(lists_data: list) -> List[str]:
    requirements = []
    for section in lists_data:
        text = section.get("text", "").lower()
        if any(kw in text for kw in ["requirements", "qualifications", "you bring", "you have", "looking for"]):
            content = section.get("content", [])
            for item in content:
                clean = re.sub(r'<[^>]+>', '', item).strip()
                if clean and len(clean) > 10:
                    requirements.append(clean)
    return requirements[:8]


async def fetch_company_jobs(client: httpx.AsyncClient, company: str) -> List[Job]:
    url = BASE_URL.format(company=company)
    try:
        resp = await client.get(url, params={"mode": "json", "limit": 100}, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Lever {company}: HTTP {resp.status_code}")
            return []

        jobs_data = resp.json()
        if not isinstance(jobs_data, list):
            return []

        display_name = COMPANY_DISPLAY_NAMES.get(company, company.title())
        is_priority = company in PRIORITY_COMPANIES

        jobs = []
        for j in jobs_data:
            title = j.get("text", "")
            if not is_relevant_role(title):
                continue

            # Location
            categories = j.get("categories", {})
            location = categories.get("location", "Not specified")
            commitment = categories.get("commitment", "")  # Full-time, Internship

            # Skip internships for now
            if "intern" in title.lower() or "intern" in commitment.lower():
                continue

            # Posted at (Lever uses millisecond timestamps)
            created_at_ms = j.get("createdAt")
            posted_at = None
            if created_at_ms:
                try:
                    posted_at = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc)
                    age_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
                    if age_hours > 168:
                        continue
                except Exception:
                    pass

            # Extract text
            description_html = j.get("descriptionBody", j.get("description", ""))
            description_text = re.sub(r'<[^>]+>', ' ', description_html)[:3000]

            lists_data = j.get("lists", [])
            requirements = extract_requirements_from_lever(lists_data)

            job_type = "data-engineering" if is_data_role(title) else "software-engineering"
            job_url = j.get("hostedUrl", f"https://jobs.lever.co/{company}/{j.get('id', '')}")

            jobs.append(Job(
                id=f"lv_{company}_{j.get('id', '')}",
                title=title,
                company=display_name,
                location=location,
                posted_at=posted_at,
                url=job_url,
                description=description_text,
                requirements=requirements,
                source="lever",
                applicant_count=None,
                job_type=job_type,
                is_priority=is_priority,
                remote=is_remote(location),
            ))

        return jobs

    except Exception as e:
        logger.error(f"Lever fetch error for {company}: {e}")
        return []


async def fetch_all_lever_jobs(companies: List[str]) -> List[Job]:
    async with httpx.AsyncClient(headers={"User-Agent": "JobHunterBot/1.0"}) as client:
        tasks = [fetch_company_jobs(client, company) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs = []
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)

    return all_jobs
