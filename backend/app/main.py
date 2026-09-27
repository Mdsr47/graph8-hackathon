import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import db

# Import Routers
from app.routers import (
    campaigns,
    prospects,
    variants,
    inbox,
    decisions,
    approvals,
    reference_emails,
    settings as settings_router,
    webhooks,
    events,
    mailboxes,
    analytics,
    auth
)
from app.services.scheduler_service import scheduler_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing graph8 Self-Healing Outbound Agent...")
    try:
        await db.init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"[Lifespan] Error initializing database: {e}", exc_info=True)

    is_serverless = any(os.environ.get(k) for k in ("VERCEL", "VERCEL_ENV", "AWS_LAMBDA_FUNCTION_NAME"))
    if not is_serverless:
        try:
            await scheduler_service.start()
            logger.info("Automated daily scheduler initialized successfully.")
        except Exception as e:
            logger.warning(f"[Lifespan] Scheduler not started: {e}")
    else:
        logger.info("Serverless environment detected: background scheduler loop disabled to prevent function freezes.")

    yield

    if not is_serverless:
        try:
            await scheduler_service.stop()
            logger.info("Shutting down agent backend.")
        except Exception:
            pass

app = FastAPI(
    title="graph8 Self-Healing Outbound Agent",
    description="Autonomous RevOps Outbound Agent powered by graph8, LangGraph, and Groq LLM",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi import FastAPI, Request

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def ensure_db_initialized_middleware(request: Request, call_next):
    try:
        await db.ensure_initialized()
    except Exception as e:
        logger.error(f"[Middleware] DB ensure_initialized error: {e}")
    response = await call_next(request)
    return response

# Register API Routers
app.include_router(campaigns.router)
app.include_router(prospects.router)
app.include_router(variants.router)
app.include_router(inbox.router)
app.include_router(decisions.router)
app.include_router(approvals.router)
app.include_router(reference_emails.router)
app.include_router(settings_router.router)
app.include_router(webhooks.router)
app.include_router(events.router)
app.include_router(mailboxes.router)
app.include_router(analytics.router)
app.include_router(auth.router)

@app.get("/api/stats")
async def get_overview_stats():
    """Returns 100% real aggregate KPI metrics directly from SQLite database."""
    return await db.get_overview_stats()

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "graph8-self-healing-agent",
        "simulation_mode": settings.SIMULATION_MODE
    }
