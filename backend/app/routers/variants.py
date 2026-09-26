from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.database import db

router = APIRouter(prefix="/api/variants", tags=["variants"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_variants(campaign_id: Optional[str] = Query(None)):
    variants = await db.get_variants(campaign_id)
    enriched = []
    for v in variants:
        sends = v.get("sends_count", 0)
        opens = v.get("opens_count", 0)
        replies = v.get("replies_count", 0)
        pos = v.get("positive_replies_count", 0)

        enriched.append({
            **v,
            "open_rate": round((opens / sends * 100), 1) if sends > 0 else 0.0,
            "reply_rate": round((replies / sends * 100), 1) if sends > 0 else 0.0,
            "positive_reply_rate": round((pos / sends * 100), 1) if sends > 0 else 0.0,
        })
    return enriched

@router.post("/{variant_id}/kill")
async def kill_variant_endpoint(variant_id: str):
    await db.kill_variant(variant_id)
    return {"status": "killed", "variant_id": variant_id}
