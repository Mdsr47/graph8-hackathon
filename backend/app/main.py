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
    events
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing graph8 Self-Healing Outbound Agent...")
    await db.init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down agent backend.")

app = FastAPI(
    title="graph8 Self-Healing Outbound Agent",
    description="Autonomous RevOps Outbound Agent powered by graph8, LangGraph, and Groq LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "graph8-self-healing-agent",
        "simulation_mode": settings.SIMULATION_MODE
    }
