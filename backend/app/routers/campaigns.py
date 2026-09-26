import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from app.database import db
from app.models.campaign import Campaign, CampaignCreate
from app.agent.workflow import run_campaign_initiation

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_all_campaigns():
    campaigns = await db.get_campaigns()
    # Enrich each with quick metrics
    result = []
    for c in campaigns:
        variants = await db.get_variants(c["id"])
        contacts = await db.get_contacts(c["id"])
        total_sends = sum(v.get("sends_count", 0) for v in variants)
        total_replies = sum(v.get("replies_count", 0) for v in variants)
        total_positive = sum(v.get("positive_replies_count", 0) for v in variants)
        total_meetings = sum(v.get("meetings_count", 0) for v in variants)

        result.append({
            **c,
            "contacts_count": len(contacts),
            "variants_count": len(variants),
            "total_sends": total_sends,
            "total_replies": total_replies,
            "total_positive": total_positive,
            "total_meetings": total_meetings,
            "reply_rate": round((total_replies / total_sends * 100), 1) if total_sends > 0 else 0.0
        })
    return result

@router.post("", response_model=Dict[str, Any])
async def create_campaign(req: CampaignCreate, background_tasks: BackgroundTasks):
    icp_dict = req.icp_filters.dict() if req.icp_filters else {
        "industry": "B2B SaaS / Technology",
        "target_titles": ["VP Sales", "Head of Sales", "CRO"],
        "keywords": ["sales automation", "outbound intelligence"]
    }

    camp = await db.create_campaign({
        "name": req.name,
        "status": "active",
        "icp_filters": icp_dict,
        "reference_email_ids": req.reference_email_ids or [],
        "daily_limit": req.daily_limit or 50,
        "target_contacts_limit": req.target_contacts_limit or 50
    })

    # Run LangGraph discovery & variant generation workflow in background
    background_tasks.add_task(run_campaign_initiation, camp["id"], icp_dict)
    return camp

@router.post("/{campaign_id}/run-daily-batch")
async def run_daily_batch(campaign_id: str):
    from app.services.scheduler_service import scheduler_service
    res = await scheduler_service.process_daily_batch(campaign_id)
    return res

@router.get("/{campaign_id}")
async def get_campaign_detail(campaign_id: str):
    camp = await db.get_campaign(campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")

    variants = await db.get_variants(campaign_id)
    contacts = await db.get_contacts(campaign_id)
    decisions = await db.get_decisions(campaign_id, limit=20)

    return {
        "campaign": camp,
        "variants": variants,
        "contacts": contacts,
        "decisions": decisions
    }

@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str):
    await db.update_campaign_status(campaign_id, "paused")
    return {"status": "paused", "campaign_id": campaign_id}

@router.post("/{campaign_id}/resume")
async def resume_campaign(campaign_id: str):
    await db.update_campaign_status(campaign_id, "active")
    return {"status": "active", "campaign_id": campaign_id}
