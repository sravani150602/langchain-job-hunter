"""
Jobright.ai fetcher — primary job source.
newgrad-jobs.com is powered by jobright.ai, so we go straight to the source.

Strategy:
1. Fetch listing pages → extract job IDs from JSON-LD structured data
2. Fetch each job detail page → full details (title, company, salary, posted_at)
3. Filter for entry-level / new-grad / FAANG roles
LangSmith traces all fetches automatically via LANGCHAIN_TRACING_V2.
"""
import httpx
import asyncio
import json
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup

from ..models import Job

logger = logging.getLogger(__name__)

BASE_URL = "https://jobright.ai"

# Listing pages — publicly accessible, no auth needed
LISTING_PAGES = [
    # ── New grad / entry level (highest priority) ──
    "/jobs/New-Grad-Software-Engineer-Jobs",
    "/jobs/Entry-Level-Software-Engineer-Jobs",
    "/jobs/New-Grad-Data-Engineer-Jobs",
    "/jobs/Entry-Level-Data-Engineer-Jobs",
    # ── FAANG company specific pages ──
    "/jobs/Google-Software-Engineer-Jobs",
    "/jobs/Meta-Software-Engineer-Jobs",
    "/jobs/Amazon-Software-Engineer-Jobs",
    "/jobs/Apple-Software-Engineer-Jobs",
    "/jobs/Microsoft-Software-Engineer-Jobs",
    "/jobs/Netflix-Software-Engineer-Jobs",
    "/jobs/Nvidia-Software-Engineer-Jobs",
    "/jobs/Uber-Software-Engineer-Jobs",
    "/jobs/Stripe-Software-Engineer-Jobs",
    "/jobs/Airbnb-Software-Engineer-Jobs",
    # ── Broad SWE / DE categories ──
    "/jobs/Software-Engineer-Jobs",
    "/jobs/Data-Engineer-Jobs",
    "/jobs/Backend-Engineer-Jobs",
    "/jobs/Full-Stack-Engineer-Jobs",
]

PRIORITY_COMPANIES = {
    "google", "meta", "amazon", "apple", "microsoft", "netflix",
    "nvidia", "paypal", "uber", "stripe", "airbnb", "databricks",
    "snowflake", "openai", "anthropic", "salesforce", "adobe",
    "linkedin", "twitter", "x corp", "reddit", "discord", "coinbase",
    "robinhood", "lyft", "doordash", "figma", "scale ai"
}

NEW_GRAD_KEYWORDS = [
    "new grad", "new graduate", "entry level", "entry-level",
    "junior", "associate", "0-1 year", "0-2 year", "recent grad",
    "university grad", "campus hire", "2024", "2025", "2026",
    "no experience required"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def is_priority_company(company: str) -> bool:
    return any(p in company.lower() for p in PRIORITY_COMPANIES)


def is_new_grad_role(title: str, description: str = "") -> bool:
    text = (title + " " + description).lower()
    return any(kw in text for kw in NEW_GRAD_KEYWORDS)


def is_senior_only(title: str) -> bool:
    """Skip clearly senior roles."""
    title_lower = title.lower()
    senior_only = ["senior", "sr.", "staff", "principal", "director", "vp ", "vice president", "lead ", "manager", "architect"]
    return any(s in title_lower for s in senior_only)


def extract_job_ids_from_jsonld(html: str) -> List[str]:
    """Extract job IDs from JSON-LD ItemList embedded in the page."""
    job_ids = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        for script in scripts:
            try:
                data = json.loads(script.string or "")
                if data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        url = item.get("url", "")
                        match = re.search(r"/jobs/info/([a-f0-9]+)", url)
                        if match:
                            job_ids.append(match.group(1))
            except Exception:
                continue
    except Exception as e:
        logger.error(f"JSON-LD extraction error: {e}")
    return job_ids


def parse_job_detail(html: str, job_id: str) -> Optional[dict]:
    """Parse a job detail page into structured data."""
    soup = BeautifulSoup(html, "html.parser")

    # Try JSON-LD first (most reliable)
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            if data.get("@type") == "JobPosting":
                # Posted date
                posted_at = None
                date_str = data.get("datePosted") or data.get("dateModified")
                if date_str:
                    try:
                        posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

                # Salary
                salary_min = salary_max = None
                comp = data.get("baseSalary", {})
                if comp and isinstance(comp, dict):
                    val = comp.get("value", {})
                    if isinstance(val, dict):
                        salary_min = val.get("minValue")
                        salary_max = val.get("maxValue")

                # Location
                loc_data = data.get("jobLocation", {})
                if isinstance(loc_data, dict):
                    addr = loc_data.get("address", {})
                    city = addr.get("addressLocality", "")
                    state = addr.get("addressRegion", "")
                    location = f"{city}, {state}".strip(", ") or "Not specified"
                else:
                    location = str(loc_data) if loc_data else "Not specified"

                # Remote
                remote_str = data.get("jobLocationType", "")
                is_remote = "remote" in (remote_str + location).lower()

                description_html = data.get("description", "")
                description_text = re.sub(r'<[^>]+>', ' ', description_html).strip()
                description_text = re.sub(r'\s+', ' ', description_text)[:3000]

                return {
                    "title": data.get("title", ""),
                    "company": data.get("hiringOrganization", {}).get("name", "") if isinstance(data.get("hiringOrganization"), dict) else "",
                    "location": location,
                    "is_remote": is_remote,
                    "posted_at": posted_at,
                    "description": description_text,
                    "requirements": extract_requirements_from_text(description_text),
                    "salary_min": int(salary_min) if salary_min else None,
                    "salary_max": int(salary_max) if salary_max else None,
                    "employment_type": data.get("employmentType", "FULL_TIME"),
                    "url": f"{BASE_URL}/jobs/info/{job_id}",
                }
        except Exception:
            continue

    # Fallback: parse HTML directly
    try:
        title_el = soup.find("h1") or soup.find(class_=re.compile(r"job-title|title"))
        title = title_el.get_text(strip=True) if title_el else ""

        return {
            "title": title,
            "company": "",
            "location": "Not specified",
            "is_remote": False,
            "posted_at": None,
            "description": soup.get_text()[:2000],
            "requirements": [],
            "salary_min": None,
            "salary_max": None,
            "employment_type": "FULL_TIME",
            "url": f"{BASE_URL}/jobs/info/{job_id}",
        }
    except Exception:
        return None


def extract_requirements_from_text(text: str) -> List[str]:
    """Extract bullet-point requirements from job description text."""
    requirements = []
    lines = text.split('. ')
    capture = False
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in ["qualifications", "requirements", "what you", "you have", "you bring"]):
            capture = True
        if capture and len(line) > 20 and len(line) < 200:
            req = line.strip().lstrip('•·-* ')
            if req:
                requirements.append(req)
        if len(requirements) >= 6:
            break
    return requirements[:6]


async def fetch_listing_page(client: httpx.AsyncClient, path: str) -> List[str]:
    """Fetch a listing page and return job IDs."""
    try:
        resp = await client.get(f"{BASE_URL}{path}", timeout=20)
        if resp.status_code != 200:
            logger.warning(f"Listing page {path}: HTTP {resp.status_code}")
            return []
        return extract_job_ids_from_jsonld(resp.text)
    except Exception as e:
        logger.error(f"Error fetching listing {path}: {e}")
        return []


async def fetch_job_detail(client: httpx.AsyncClient, job_id: str, semaphore: asyncio.Semaphore) -> Optional[Job]:
    """Fetch and parse a single job detail page."""
    async with semaphore:
        try:
            url = f"{BASE_URL}/jobs/info/{job_id}"
            resp = await client.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            detail = parse_job_detail(resp.text, job_id)
            if not detail or not detail["title"] or not detail["company"]:
                return None

            title = detail["title"]
            company = detail["company"]

            # Filter: skip clearly senior roles (unless FAANG)
            if is_senior_only(title) and not is_priority_company(company):
                return None

            # Skip jobs posted more than 7 days ago
            if detail["posted_at"]:
                age_hours = (datetime.now(timezone.utc) - detail["posted_at"]).total_seconds() / 3600
                if age_hours > 168:
                    return None

            job_type = "data-engineering" if "data engineer" in title.lower() else "software-engineering"

            return Job(
                id=f"jr_{job_id}",
                title=title,
                company=company,
                location=detail["location"],
                posted_at=detail["posted_at"],
                url=detail["url"],
                description=detail["description"],
                requirements=detail["requirements"],
                source="jobright",
                applicant_count=None,
                job_type=job_type,
                is_priority=is_priority_company(company),
                remote=detail["is_remote"],
                salary_min=detail["salary_min"],
                salary_max=detail["salary_max"],
            )

        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {e}")
            return None


async def fetch_jobright_jobs(max_jobs: int = 80) -> List[Job]:
    """
    Main entry point — fetches fresh jobs from jobright.ai.
    Respects rate limits with concurrency limiting.
    """
    logger.info("Fetching job listings from jobright.ai...")

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Step 1: Collect job IDs from all listing pages (in parallel)
        listing_tasks = [fetch_listing_page(client, path) for path in LISTING_PAGES]
        listing_results = await asyncio.gather(*listing_tasks, return_exceptions=True)

        # Deduplicate job IDs
        seen_ids = set()
        all_job_ids = []
        for result in listing_results:
            if isinstance(result, list):
                for jid in result:
                    if jid not in seen_ids:
                        seen_ids.add(jid)
                        all_job_ids.append(jid)

        logger.info(f"Found {len(all_job_ids)} unique job IDs from jobright.ai listing pages")

        # Limit to avoid hammering the server
        job_ids_to_fetch = all_job_ids[:max_jobs]

        # Step 2: Fetch job details with rate limiting (max 10 concurrent)
        semaphore = asyncio.Semaphore(10)
        detail_tasks = [fetch_job_detail(client, jid, semaphore) for jid in job_ids_to_fetch]
        detail_results = await asyncio.gather(*detail_tasks, return_exceptions=True)

    # Filter out None results
    jobs = [j for j in detail_results if isinstance(j, Job)]
    logger.info(f"Successfully fetched {len(jobs)} jobs from jobright.ai")
    return jobs
