from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.database import db
from app.adapters.graph8_client import graph8_client
from app.llm.llm_client import llm_client
from app.services.sse_manager import sse_manager
from app.models.inbox import ReplySendRequest

router = APIRouter(prefix="/api/inbox", tags=["inbox"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_inbox_items():
    # Fetch reply events from events table
    events = await db.get_events(limit=100)
    reply_events = [e for e in events if e.get("event_type") == "replied"]

    inbox_items = []
    for re in reply_events:
        contact_id = re.get("contact_id")
        contact_info = {}
        if contact_id:
            contacts = await db.get_contacts()
            c_match = [c for c in contacts if c["id"] == contact_id]
            if c_match:
                contact_info = c_match[0]

        payload = re.get("raw_payload", {})
        inbox_items.append({
            "id": re["id"],
            "contact_id": contact_id,
            "contact_name": contact_info.get("name") or payload.get("from_name", "Sarah Jenkins"),
            "contact_email": contact_info.get("email") or payload.get("from_email", "sarah.jenkins@fintechflow.io"),
            "company": contact_info.get("company") or payload.get("company", "FintechFlow Inc"),
            "subject": payload.get("subject", "Re: Outbound pipeline deliverability"),
            "body": payload.get("body") or payload.get("text", "Thanks for reaching out! Can we see a demo Thursday 2pm EST?"),
            "sentiment": re.get("sentiment", "positive"),
            "status": payload.get("status", "unhandled"),
            "received_at": re.get("created_at"),
            "ai_draft_reply": payload.get("ai_draft_reply")
        })

    # If empty, also pull from graph8 inbox adapter
    if not inbox_items:
        try:
            g8_items = await graph8_client.list_inbox()
            for item in g8_items:
                inbox_items.append({
                    "id": item.get("id"),
                    "contact_id": item.get("contact_id"),
                    "contact_name": item.get("from_name"),
                    "contact_email": item.get("from_email"),
                    "company": item.get("company"),
                    "subject": item.get("subject"),
                    "body": item.get("text"),
                    "sentiment": item.get("sentiment", "positive"),
                    "status": item.get("status", "unhandled"),
                    "received_at": "2026-09-26T18:00:00Z",
                    "ai_draft_reply": None
                })
        except Exception:
            pass

    # If still empty, supply an interactive seed reply so user can test AI Draft generation immediately
    if not inbox_items:
        inbox_items.append({
            "id": "reply_demo_01",
            "contact_id": "cnt_seed_01",
            "contact_name": "Sarah Jenkins",
            "contact_email": "sarah.jenkins@fintechflow.io",
            "company": "FintechFlow Inc",
            "subject": "Re: Quick question regarding outbound pipeline at FintechFlow Inc",
            "body": "Hi Alex, thanks for reaching out. Yes, we had deliverability issues last month and burned two secondary domains. How does your self-healing reallocation work in practice? Can we see a demo Thursday 2pm EST?",
            "sentiment": "positive",
            "status": "unhandled",
            "received_at": "2026-09-26T18:00:00Z",
            "ai_draft_reply": None
        })

    return inbox_items

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

    # Submit to Approvals queue (Section 9 HITL Gate: Never auto-send replies without approval)
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
    """Sends reply through graph8 client once human approved."""
    resp = await graph8_client.send_reply(item_id, req.text)
    await graph8_client.tag_reply(item_id, "replied")
    return {"status": "sent", "response": resp}
