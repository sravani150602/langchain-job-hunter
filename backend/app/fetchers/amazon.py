"""
Amazon Jobs API - direct from amazon.jobs
Amazon uses a public JSON API endpoint for their job search.
"""
import httpx
from datetime import datetime, timezone
from typing import List, Optional
from ..models import Job
import logging
import re

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.amazon.jobs/en/search.json"

TARGET_CATEGORIES = [
    "software-development",
    "data-science",
    "machine-learning-science",
]

ROLE_KEYWORDS = [
    "software engineer", "software development engineer", "sde",
    "data engineer", "frontend engineer", "backend engineer",
    "new grad", "university grad", "entry level"
]


def is_relevant(title: str) -> bool:
    return any(kw in title.lower() for kw in ROLE_KEYWORDS)


def parse_amazon_date(date_str: str) -> Optional[datetime]:
    """Amazon uses format like 'November 15, 2024' or ISO."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        pass
    try:
        return datetime.strptime(date_str, "%B %d, %Y").replace(tzinfo=timezone.utc)
    except Exception:
        pass
    return None


async def fetch_amazon_jobs() -> List[Job]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*",
        "Referer": "https://www.amazon.jobs/en/search",
    }

    all_jobs = []
    seen_ids = set()

    queries = [
        "software development engineer new graduate",
        "data engineer new graduate",
        "software engineer entry level",
    ]

    async with httpx.AsyncClient(headers=headers) as client:
        for query in queries:
            try:
                params = {
                    "base_query": query,
                    "sort": "recent",
                    "result_limit": 20,
                    "category[]": ["software-development"],
                }
                resp = await client.get(SEARCH_URL, params=params, timeout=15)
                if resp.status_code != 200:
                    logger.warning(f"Amazon jobs HTTP {resp.status_code}")
                    continue

                data = resp.json()
                jobs_list = data.get("jobs", [])

                for j in jobs_list:
                    job_id = str(j.get("id", ""))
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title = j.get("title", "")
                    if not is_relevant(title):
                        continue

                    location = j.get("location", "Not specified")
                    posted_at = parse_amazon_date(j.get("posted_date", ""))

                    # Skip jobs older than 7 days
                    if posted_at:
                        age_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
                        if age_hours > 168:
                            continue

                    description = j.get("description", j.get("job_summary", ""))
                    description_clean = re.sub(r'<[^>]+>', ' ', description)[:3000]

                    basic_qualifications = j.get("basic_qualifications", "")
                    requirements = []
                    if basic_qualifications:
                        for line in basic_qualifications.split('\n'):
                            clean = line.strip().lstrip('•- ')
                            if clean and len(clean) > 10:
                                requirements.append(clean)
                    requirements = requirements[:8]

                    job_url = f"https://www.amazon.jobs/en/jobs/{job_id}"
                    team = j.get("team", {})
                    label = team.get("label", "Amazon") if team else "Amazon"

                    job_type = "data-engineering" if "data engineer" in title.lower() else "software-engineering"

                    all_jobs.append(Job(
                        id=f"amz_{job_id}",
                        title=title,
                        company=f"Amazon ({label})" if label != "Amazon" else "Amazon",
                        location=location,
                        posted_at=posted_at,
                        url=job_url,
                        description=description_clean,
                        requirements=requirements,
                        source="amazon",
                        applicant_count=None,
                        job_type=job_type,
                        is_priority=True,
                        remote="remote" in location.lower(),
                    ))

            except Exception as e:
                logger.error(f"Amazon fetch error for '{query}': {e}")

    return all_jobs
