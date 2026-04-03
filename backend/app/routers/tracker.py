"""
Application tracker CRUD endpoints.
Stores applications in memory for demo; swap job_store pattern for DB in production.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException

from ..models import TrackerEntry, TrackerUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tracker", tags=["tracker"])

# In-memory store
_tracker: dict[str, TrackerEntry] = {}

VALID_STATUSES = {"saved", "applied", "interviewing", "offer", "rejected"}


@router.get("/", response_model=List[TrackerEntry])
async def get_all_applications():
    """Get all tracked applications sorted by updated_at desc."""
    entries = sorted(_tracker.values(), key=lambda e: e.updated_at, reverse=True)
    return entries


@router.post("/", response_model=TrackerEntry)
async def add_application(entry: TrackerEntry):
    """Add a new job application to the tracker."""
    entry.id = str(uuid.uuid4())
    entry.created_at = datetime.now(timezone.utc)
    entry.updated_at = datetime.now(timezone.utc)
    _tracker[entry.id] = entry
    logger.info(f"Tracking new application: {entry.job_title} at {entry.company}")
    return entry


@router.patch("/{entry_id}", response_model=TrackerEntry)
async def update_application(entry_id: str, update: TrackerUpdate):
    """Update the status or notes of a tracked application."""
    entry = _tracker.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Application not found")

    if update.status is not None:
        if update.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}"
            )
        entry.status = update.status

    if update.notes is not None:
        entry.notes = update.notes

    entry.updated_at = datetime.now(timezone.utc)
    _tracker[entry_id] = entry
    return entry


@router.delete("/{entry_id}")
async def delete_application(entry_id: str):
    """Remove an application from the tracker."""
    if entry_id not in _tracker:
        raise HTTPException(status_code=404, detail="Application not found")
    del _tracker[entry_id]
    return {"deleted": entry_id}


@router.get("/stats")
async def get_tracker_stats():
    """Get application pipeline statistics."""
    entries = list(_tracker.values())
    stats = {s: 0 for s in VALID_STATUSES}
    for e in entries:
        if e.status in stats:
            stats[e.status] += 1
    return {
        "total": len(entries),
        "by_status": stats,
    }
