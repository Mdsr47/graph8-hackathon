from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database import db
from app.adapters.graph8_client import graph8_client
from app.services.email_service import EmailService
from app.llm.llm_client import llm_client
from app.services.sse_manager import sse_manager
import logging

logger = logging.getLogger("inbox_router")
router = APIRouter(prefix="/api/inbox", tags=["inbox"])

class DirectSendRequest(BaseModel):
    to_email: str
    subject: str
    body: str

class ReplySendRequest(BaseModel):
    text: str

@router.get("", response_model=List[Dict[str, Any]])
async def get_inbox_items():
    """Returns real inbox messages from SQLite database and synced IMAP."""
    # 1. Fetch from inbox_messages table
    db_messages = await db.get_inbox_messages(limit=50)
    if db_messages:
        return db_messages

    # 2. Fallback to events table if any webhook replies were logged
    events = await db.get_events(limit=100)
    reply_events = [e for e in events if e.get("event_type") == "replied"]

    inbox_items = []
    if reply_events:
        contacts = await db.get_contacts()
        contacts_by_id = {c["id"]: c for c in contacts}

        for re in reply_events:
            contact_id = re.get("contact_id")
            contact_info = contacts_by_id.get(contact_id, {})
            payload = re.get("raw_payload", {})

            inbox_items.append({
                "id": re["id"],
                "contact_id": contact_id,
                "contact_name": contact_info.get("name") or payload.get("from_name", "Inbound Contact"),
                "contact_email": contact_info.get("email") or payload.get("from_email", "prospect@example.com"),
                "company": contact_info.get("company") or payload.get("company", "Enterprise Account"),
                "subject": payload.get("subject", "Re: Outbound pipeline inquiry"),
                "body": payload.get("body") or payload.get("text", "Thanks for reaching out."),
                "sentiment": re.get("sentiment", "positive"),
                "status": payload.get("status", "unhandled"),
                "received_at": re.get("created_at"),
                "ai_draft_reply": payload.get("ai_draft_reply")
            })

    return inbox_items

@router.post("/compose")
async def compose_and_send_email(req: DirectSendRequest):
    """Sends a real email directly via the user's configured SMTP server."""
    mailbox = await db.get_mailbox_settings()
    if not mailbox or not mailbox.get("smtp_username"):
        raise HTTPException(
            status_code=400,
            detail="SMTP is not configured yet. Please configure your email credentials in the Settings page first."
        )

    try:
        result = EmailService.send_email(
            settings=mailbox,
            to_email=req.to_email,
            subject=req.subject,
            body=req.body
        )

        # Log outbound send in events table
        await db.create_event({
            "event_type": "sent",
            "raw_payload": {
                "to_email": req.to_email,
                "subject": req.subject,
                "body": req.body,
                "direct_compose": True
            }
        })

        await sse_manager.broadcast("email_sent", result)
        return {"success": True, "message": f"Email successfully delivered to {req.to_email} via SMTP!", "details": result}
    except Exception as e:
        logger.error(f"Error sending email via SMTP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.post("/{item_id}/draft")
async def generate_draft_reply(item_id: str):
    """Generates an intelligent context-aware reply using LLM."""
    inbox = await get_inbox_items()
    matched = [i for i in inbox if i["id"] == item_id]
    if not matched:
        raise HTTPException(status_code=404, detail="Inbox item not found")

    item = matched[0]
    draft = llm_client.draft_reply(
        original_pitch="Outbound deliverability self-healing engine",
        prospect_reply=item["body"],
        prospect_name=item["contact_name"],
        company=item["company"]
    )

    # Save draft into database
    await db.update_inbox_message_draft(item_id, draft)

    # Submit to Approvals queue (Section 9 HITL Gate: Supervised before sending)
    approval = await db.create_approval({
        "type": "reply_draft",
        "payload": {
            "inbox_item_id": item_id,
            "to_name": item["contact_name"],
            "to_email": item["contact_email"],
            "company": item["company"],
            "subject": f"Re: {item['subject']}",
            "draft_body": draft
        },
        "status": "pending"
    })

    await sse_manager.broadcast("approval_created", approval)

    return {
        "item_id": item_id,
        "ai_draft_reply": draft,
        "approval_id": approval["id"],
        "status": "pending_approval"
    }

@router.post("/{item_id}/send")
async def send_inbox_reply(item_id: str, req: ReplySendRequest):
    """Sends reply through real user SMTP or graph8 client."""
    inbox = await get_inbox_items()
    matched = [i for i in inbox if i["id"] == item_id]
    to_email = matched[0]["contact_email"] if matched else None
    subj = matched[0]["subject"] if matched else "Re: Outbound"
    if not subj.startswith("Re:"):
        subj = f"Re: {subj}"

    mailbox = await db.get_mailbox_settings()
    sent_via_smtp = False
    error_msg = None

    if mailbox and mailbox.get("smtp_username") and to_email:
        try:
            EmailService.send_email(
                settings=mailbox,
                to_email=to_email,
                subject=subj,
                body=req.text
            )
            sent_via_smtp = True
        except Exception as e:
            logger.warning(f"SMTP send failed, falling back to graph8: {e}")
            error_msg = str(e)

    if not sent_via_smtp:
        # Fallback to graph8 client
        await graph8_client.send_reply(item_id, req.text)

    await db.update_inbox_message_status(item_id, "replied")

    # Record event
    await db.create_event({
        "event_type": "sent",
        "raw_payload": {
            "inbox_item_id": item_id,
            "to_email": to_email,
            "reply_text": req.text,
            "via_smtp": sent_via_smtp
        }
    })

    return {
        "status": "sent",
        "via_smtp": sent_via_smtp,
        "smtp_error": error_msg if not sent_via_smtp else None
    }
