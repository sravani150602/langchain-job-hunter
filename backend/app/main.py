from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from .config import settings
from .routers.jobs import router as jobs_router
from .routers.resume import router as resume_router
from .routers.tracker import router as tracker_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Adzuna configured: {bool(settings.adzuna_app_id)}")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    description="CareerCopilot AI — LangChain-powered job search and career prep platform for students",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
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
