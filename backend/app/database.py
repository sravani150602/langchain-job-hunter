"""
In-memory job store with optional DynamoDB backend for AWS deployment.
Locally: stores jobs in memory with a simple dict.
Production (AWS): uses DynamoDB for persistence across Lambda invocations.
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict
from .models import Job
import logging

logger = logging.getLogger(__name__)

USE_DYNAMODB = os.getenv("USE_DYNAMODB", "false").lower() == "true"
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "job-hunter-jobs")


class InMemoryJobStore:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._last_refresh: Optional[datetime] = None

    def save_jobs(self, jobs: List[Job]):
        for job in jobs:
            self._jobs[job.id] = job
        self._last_refresh = datetime.now(timezone.utc)
        logger.info(f"Saved {len(jobs)} jobs. Total in store: {len(self._jobs)}")

    def get_all_jobs(self) -> List[Job]:
        return list(self._jobs.values())

    def get_jobs_filtered(
        self,
        max_hours_ago: int = 48,
        job_type: Optional[str] = None,
        priority_only: bool = False,
        remote_only: bool = False,
        min_score: int = 0,
    ) -> List[Job]:
        jobs = list(self._jobs.values())

        if max_hours_ago:
            jobs = [j for j in jobs if j.hours_ago is None or j.hours_ago <= max_hours_ago]

        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]

        if priority_only:
            jobs = [j for j in jobs if j.is_priority]

        if remote_only:
            jobs = [j for j in jobs if j.remote]

        if min_score > 0:
            jobs = [j for j in jobs if (j.match_score or 0) >= min_score]

        return jobs

    def clear(self):
        self._jobs.clear()

    @property
    def last_refresh(self) -> Optional[datetime]:
        return self._last_refresh

    @property
    def total_count(self) -> int:
        return len(self._jobs)


class DynamoDBJobStore:
    def __init__(self):
        import boto3
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(DYNAMODB_TABLE)

    def save_jobs(self, jobs: List[Job]):
        with self.table.batch_writer() as batch:
            for job in jobs:
                item = job.model_dump(mode="json")
                item["posted_at"] = item["posted_at"].isoformat() if item.get("posted_at") else None
                batch.put_item(Item=item)
        logger.info(f"Saved {len(jobs)} jobs to DynamoDB")

    def get_all_jobs(self) -> List[Job]:
        response = self.table.scan()
        jobs = []
        for item in response.get("Items", []):
            if item.get("posted_at"):
                item["posted_at"] = datetime.fromisoformat(item["posted_at"])
            jobs.append(Job(**item))
        return jobs

    def get_jobs_filtered(self, **kwargs) -> List[Job]:
        # For simplicity, fetch all and filter in memory
        # In production you'd use DynamoDB query with GSI
        all_jobs = self.get_all_jobs()
        store = InMemoryJobStore()
        store.save_jobs(all_jobs)
        return store.get_jobs_filtered(**kwargs)

    def clear(self):
        pass  # Don't clear DynamoDB - just overwrite

    @property
    def last_refresh(self):
        return None

    @property
    def total_count(self):
        return self.table.item_count


# Singleton job store
if USE_DYNAMODB:
    try:
        job_store = DynamoDBJobStore()
        logger.info("Using DynamoDB job store")
    except Exception as e:
        logger.warning(f"DynamoDB init failed, falling back to in-memory: {e}")
        job_store = InMemoryJobStore()
else:
    job_store = InMemoryJobStore()
