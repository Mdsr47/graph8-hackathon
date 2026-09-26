import logging
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.adapters.graph8_client import graph8_client
from app.database import db
from app.llm.llm_client import llm_client
from app.services.sse_manager import sse_manager
from app.agent.workflow import trigger_feedback_cycle

logger = logging.getLogger("webhooks")
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

class WebhookSimulateRequest(BaseModel):
    campaign_id: Optional[str] = None
    contact_id: Optional[str] = None
    variant_id: Optional[str] = None
    event_type: str  # sent, opened, replied, bounced, meeting_booked
    reply_text: Optional[str] = None
    sentiment: Optional[str] = None

@router.post("/graph8")
async def receive_graph8_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_graph8_signature: Optional[str] = Header(None, alias="X-Graph8-Signature")
):
    """
    Official graph8 webhook receiver.
    Verifies HMAC signature, writes event, parses sentiment on replies,
    re-enters LangGraph workflow at feedback_node, and broadcasts over SSE.
    """
    raw_body = await request.body()

    # Verify signature if signature header is provided or not in simulation mode
    if x_graph8_signature:
        is_valid = graph8_client.verify_webhook_signature(raw_body, x_graph8_signature)
        if not is_valid and not graph8_client.simulation_mode:
            logger.warning("[Webhook] Invalid HMAC signature received")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = await request.json()
        logger.info(f"[Webhook Received] Event received from graph8: {payload}")
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON body")

    raw_event = payload.get("event") or payload.get("event_type") or payload.get("type", "unknown")
    event_lower = str(raw_event).lower().replace(" ", "_").replace(".", "_")

    # Map graph8's specific UI event names to core agent telemetry
    if "repli" in event_lower or "reply" in event_lower:
        event_type = "replied"
    elif "sent" in event_lower or "send" in event_lower:
        event_type = "sent"
    elif "click" in event_lower or "open" in event_lower:
        event_type = "opened"
    elif "bounce" in event_lower:
        event_type = "bounced"
    elif "meet" in event_lower or "book" in event_lower:
        event_type = "meeting_booked"
    elif "enroll" in event_lower:
        event_type = "enrolled"
    elif "intent" in event_lower or "signal" in event_lower:
        event_type = "intent_signal"
    else:
        event_type = event_lower

    # Extract IDs and fields from top-level or nested data
    inner_data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    contact_id = payload.get("contact_id") or inner_data.get("contact_id") or inner_data.get("contact", {}).get("id")
    variant_id = payload.get("variant_id") or inner_data.get("variant_id")
    campaign_id = payload.get("campaign_id") or inner_data.get("campaign_id")

    sentiment = payload.get("sentiment") or inner_data.get("sentiment")
    # If inbound prospect reply, run LLM sentiment classifier
    if event_type == "replied":
        reply_text = payload.get("text") or payload.get("body") or inner_data.get("text") or inner_data.get("body") or inner_data.get("snippet", "")
        if not sentiment and reply_text:
            sentiment_analysis = llm_client.classify_sentiment(reply_text)
            sentiment = sentiment_analysis.get("sentiment", "positive")
            payload["sentiment_analysis"] = sentiment_analysis
            inner_data["sentiment_analysis"] = sentiment_analysis

    # 1. Write to events table
    event_record = await db.create_event({
        "contact_id": contact_id,
        "variant_id": variant_id,
        "event_type": event_type,
        "raw_payload": payload,
        "sentiment": sentiment
    })

    # 2. Update variant performance telemetry
    if variant_id:
        if event_type == "opened":
            await db.increment_variant_metric(variant_id, "opens_count", 1)
        elif event_type == "replied":
            await db.increment_variant_metric(variant_id, "replies_count", 1)
            if sentiment == "positive":
                await db.increment_variant_metric(variant_id, "positive_replies_count", 1)
        elif event_type == "meeting_booked":
            await db.increment_variant_metric(variant_id, "meetings_count", 1)

    # 3. Update contact status
    if contact_id:
        if event_type in ("replied", "bounced", "meeting_booked"):
            await db.update_contact_status(contact_id, event_type)

    # 4. Broadcast live update over SSE
    await sse_manager.broadcast("webhook_event", {
        "event_id": event_record["id"],
        "event_type": event_type,
        "contact_id": contact_id,
        "variant_id": variant_id,
        "sentiment": sentiment,
        "payload": payload
    })

    # 5. Re-enter LangGraph workflow at feedback_node in background
    if campaign_id:
        background_tasks.add_task(trigger_feedback_cycle, campaign_id, event_record)

    return {"status": "accepted", "event_id": event_record["id"]}

@router.post("/simulate")
async def simulate_webhook_event(req: WebhookSimulateRequest, background_tasks: BackgroundTasks):
    """
    Simulation endpoint for live hackathon demos.
    Allows instant triggering of opens, positive replies, and booked meetings.
    """
    # Auto-resolve IDs if not provided
    campaign_id = req.campaign_id
    if not campaign_id:
        campaigns = await db.get_campaigns()
        if campaigns:
            campaign_id = campaigns[0]["id"]
        else:
            c = await db.create_campaign({"name": "Demo Outbound Campaign", "status": "active"})
            campaign_id = c["id"]

    variant_id = req.variant_id
    if not variant_id and campaign_id:
        variants = await db.get_variants(campaign_id)
        if variants:
            variant_id = variants[0]["id"]

    contact_id = req.contact_id
    if not contact_id and campaign_id:
        contacts = await db.get_contacts(campaign_id)
        if contacts:
            contact_id = contacts[0]["id"]

    reply_text = req.reply_text or "Hi Alex, thanks for reaching out. Yes, we had deliverability issues last month and burned two secondary domains. Can we see a demo Thursday 2pm EST?"
    sentiment = req.sentiment or ("positive" if req.event_type == "replied" else None)

    simulated_payload = {
        "event_type": req.event_type,
        "campaign_id": campaign_id,
        "contact_id": contact_id,
        "variant_id": variant_id,
        "text": reply_text if req.event_type == "replied" else None,
        "from_name": "Sarah Jenkins",
        "from_email": "sarah.jenkins@fintechflow.io",
        "company": "FintechFlow Inc",
        "subject": "Re: Outbound pipeline deliverability",
        "sentiment": sentiment
    }

    # Dispatch to graph8 webhook handler directly
    event_record = await db.create_event({
        "contact_id": contact_id,
        "variant_id": variant_id,
        "event_type": req.event_type,
        "raw_payload": simulated_payload,
        "sentiment": sentiment
    })

    if variant_id:
        if req.event_type == "sent":
            await db.increment_variant_metric(variant_id, "sends_count", 1)
        elif req.event_type == "opened":
            await db.increment_variant_metric(variant_id, "opens_count", 1)
        elif req.event_type == "replied":
            await db.increment_variant_metric(variant_id, "replies_count", 1)
            if sentiment == "positive":
                await db.increment_variant_metric(variant_id, "positive_replies_count", 1)
        elif req.event_type == "meeting_booked":
            await db.increment_variant_metric(variant_id, "meetings_count", 1)

    if contact_id and req.event_type in ("replied", "bounced", "meeting_booked"):
        await db.update_contact_status(contact_id, req.event_type)

    await sse_manager.broadcast("webhook_event", {
        "event_id": event_record["id"],
        "event_type": req.event_type,
        "contact_id": contact_id,
        "variant_id": variant_id,
        "sentiment": sentiment,
        "payload": simulated_payload
    })

    # Trigger feedback loop
    if campaign_id:
        background_tasks.add_task(trigger_feedback_cycle, campaign_id, event_record)

    return {
        "status": "simulated",
        "event_id": event_record["id"],
        "event_type": req.event_type,
        "sentiment": sentiment
    }
