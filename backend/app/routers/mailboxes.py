from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from app.database import db
from app.services.email_service import EmailService
from app.llm.llm_client import llm_client
from app.services.sse_manager import sse_manager
from datetime import datetime, timezone
import logging

logger = logging.getLogger("mailboxes_router")
router = APIRouter(prefix="/api/mailboxes", tags=["mailboxes"])

@router.get("/settings")
async def get_mailbox_settings():
    settings = await db.get_mailbox_settings()
    if not settings:
        return {
            "configured": False,
            "provider": "gmail",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "smtp_use_tls": True,
            "smtp_use_ssl": False,
            "imap_host": "imap.gmail.com",
            "imap_port": 993,
            "imap_username": "",
            "imap_password": "",
            "imap_use_ssl": True,
            "from_name": "RevOps Outbound Agent",
            "from_email": "",
            "status": "disconnected"
        }
    
    # Mask password for display
    display_settings = dict(settings)
    display_settings["configured"] = bool(settings.get("smtp_username") and settings.get("status") == "connected")
    if display_settings.get("smtp_password"):
        display_settings["has_password"] = True
    return display_settings

@router.post("/test-connection")
async def test_mailbox_connection(req: Dict[str, Any]):
    # If password is placeholder or omitted, pull saved password from db
    saved = await db.get_mailbox_settings() or {}
    smtp_pass = req.get("smtp_password") or saved.get("smtp_password", "")
    imap_pass = req.get("imap_password") or saved.get("imap_password", "")
    
    test_payload = {
        **req,
        "smtp_password": smtp_pass,
        "imap_password": imap_pass
    }

    result = EmailService.test_connection(test_payload)
    return result

@router.post("/settings")
async def save_mailbox_settings(req: Dict[str, Any]):
    saved = await db.get_mailbox_settings() or {}
    # Retain existing passwords if blank in request
    smtp_pass = req.get("smtp_password") if req.get("smtp_password") else saved.get("smtp_password", "")
    imap_pass = req.get("imap_password") if req.get("imap_password") else saved.get("imap_password", "")

    to_save = {
        **req,
        "smtp_password": smtp_pass,
        "imap_password": imap_pass,
        "status": "connected"
    }

    updated = await db.save_mailbox_settings(to_save)
    return {
        "success": True,
        "settings": updated
    }

@router.post("/sync")
async def sync_mailbox_inbox():
    """Connects to user's real IMAP server and ingests latest emails into database."""
    settings = await db.get_mailbox_settings()
    if not settings or not settings.get("imap_username"):
        raise HTTPException(status_code=400, detail="Mailbox IMAP is not configured. Please save credentials in Settings.")

    try:
        raw_emails = EmailService.fetch_inbox_emails(settings, limit=15)
        synced_count = 0
        contacts = await db.get_contacts()
        
        for email_item in raw_emails:
            # Check if matching contact exists
            matching_contact = None
            from_addr = email_item["from_email"].lower()
            for c in contacts:
                if c.get("email", "").lower() == from_addr:
                    matching_contact = c
                    break

            # Classify sentiment using Groq LLM
            body_text = email_item["body"]
            sentiment_analysis = llm_client.classify_sentiment(body_text)
            sentiment = sentiment_analysis.get("sentiment", "neutral")

            msg_record = await db.save_inbox_message({
                "contact_id": matching_contact["id"] if matching_contact else None,
                "contact_name": matching_contact["name"] if matching_contact else email_item["from_name"],
                "contact_email": email_item["from_email"],
                "company": matching_contact["company"] if matching_contact else (from_addr.split("@")[-1].split(".")[0].capitalize()),
                "subject": email_item["subject"],
                "body": body_text,
                "sentiment": sentiment,
                "status": "unread",
                "message_id": email_item["message_id"],
                "received_at": email_item["received_at"]
            })

            if not msg_record.get("already_exists"):
                synced_count += 1
                # Record event in events table
                await db.create_event({
                    "contact_id": matching_contact["id"] if matching_contact else None,
                    "event_type": "replied",
                    "raw_payload": {
                        "from_name": email_item["from_name"],
                        "from_email": email_item["from_email"],
                        "subject": email_item["subject"],
                        "body": body_text
                    },
                    "sentiment": sentiment
                })

        now_iso = datetime.now(timezone.utc).isoformat()
        await db.update_mailbox_sync("connected", now_iso)
        await sse_manager.broadcast("inbox_synced", {"synced_count": synced_count, "synced_at": now_iso})

        return {
            "success": True,
            "synced_count": synced_count,
            "total_fetched": len(raw_emails)
        }
    except Exception as e:
        logger.error(f"Error during IMAP sync: {e}")
        raise HTTPException(status_code=500, detail=f"IMAP sync failed: {str(e)}")
