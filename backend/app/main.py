from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import logging
import os

from .config import settings
from .routers.jobs import router as jobs_router
from .routers.resume import router as resume_router
from .routers.tracker import router as tracker_router
from .sample_jobs import get_sample_jobs
from .database import job_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def _refresh_sample_jobs_loop():
    """Reload sample jobs every 30 minutes so timestamps stay fresh."""
    while True:
        await asyncio.sleep(30 * 60)
        sample = get_sample_jobs()
        job_store.save_jobs(sample)
        logger.info(f"Refreshed {len(sample)} sample jobs (timestamp reset)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Adzuna configured: {bool(settings.adzuna_app_id)}")
    # Always pre-load sample jobs so demo works immediately
    sample = get_sample_jobs()
    job_store.save_jobs(sample)
    logger.info(f"Loaded {len(sample)} sample jobs for demo")
    # Keep sample job timestamps fresh every 30 minutes
    refresh_task = asyncio.create_task(_refresh_sample_jobs_loop())
    yield
    refresh_task.cancel()
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    description="CareerCopilot AI — LangChain-powered job search and career prep platform for students",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(resume_router)
app.include_router(tracker_router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


# Serve frontend static files in production
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
    logger.info(f"Serving frontend from {frontend_dist}")
