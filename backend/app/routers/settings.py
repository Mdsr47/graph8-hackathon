from fastapi import APIRouter
from typing import Dict, Any
from app.config import settings
from app.database import db
from app.adapters.graph8_client import graph8_client

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("")
async def get_settings():
    db_settings = await db.get_settings()
    
    # Mailbox status
    mailboxes = await graph8_client.list_mailboxes()
    active_mailbox = mailboxes[0] if mailboxes else None

    # Mask API keys
    masked_g8 = f"g8_...{settings.GRAPH8_API_KEY[-4:]}" if len(settings.GRAPH8_API_KEY) > 8 else ("Configured" if settings.GRAPH8_API_KEY else "Not Configured")
    masked_llm = f"...{settings.LLM_API_KEY[-4:]}" if len(settings.LLM_API_KEY) > 8 else ("Configured" if settings.LLM_API_KEY else "Not Configured")

    return {
        "graph8_api_key_status": masked_g8,
        "graph8_base_url": settings.GRAPH8_BASE_URL,
        "llm_provider": "Groq (OpenAI-compatible)" if "groq" in settings.LLM_BASE_URL.lower() else "OpenAI-compatible",
        "llm_model": settings.LLM_MODEL,
        "llm_base_url": settings.LLM_BASE_URL,
        "llm_api_key_status": masked_llm,
        "supabase_configured": bool(settings.SUPABASE_URL and "your-project" not in settings.SUPABASE_URL),
        "webhook_url": f"{settings.WEBHOOK_BASE_URL.rstrip('/')}/api/webhooks/graph8",
        "simulation_mode": settings.SIMULATION_MODE,
        "voice_escalation": {
            "enabled": settings.VOICE_ESCALATION_ENABLED,
            "badge": "Voice escalation: logic complete — awaiting connected number",
            "threshold": 90
        },
        "mailbox": active_mailbox or {
            "status": "not_connected",
            "provider": "gmail",
            "email": "none"
        },
        "graph8_mailbox_settings_url": "https://app.graph8.com/settings/mailboxes",
        "custom_settings": db_settings
    }

from datetime import datetime, timezone
from app.services.sse_manager import sse_manager

@router.post("")
async def update_settings(payload: Dict[str, Any]):
    for k, v in payload.items():
        await db.set_setting(k, str(v))
    return {"status": "saved"}

@router.post("/reset-database")
async def reset_database():
    """Wipes all transactional records and broadcasts database_reset event."""
    await db.reset_db()
    await sse_manager.broadcast("database_reset", {
        "status": "cleared",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "success", "message": "Database completely reset and refreshed with clean defaults."}
