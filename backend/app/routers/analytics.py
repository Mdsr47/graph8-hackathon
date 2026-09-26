from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from app.database import db
from app.adapters.graph8_client import graph8_client

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("", response_model=Dict[str, Any])
async def get_analytics(campaign_id: Optional[str] = Query(None)):
    """
    Returns full analytics data across variants, deliverability, reply rates, 
    sentiment, and intent buckets (matching Graph8 A/B test analytics schema).
    """
    data = await db.get_analytics_data(campaign_id=campaign_id)

    # If specific campaign requested and graph8 client has remote metrics, merge them
    if campaign_id and not graph8_client.simulation_mode:
        try:
            remote_variants = await graph8_client.get_variant_metrics(campaign_id)
            if remote_variants:
                # Merge remote metrics into local variant objects
                remote_map = {v.get("variantId"): v.get("metrics", {}) for v in remote_variants if "variantId" in v}
                for v in data.get("variants", []):
                    vid = v.get("variant_id")
                    if vid in remote_map:
                        rm = remote_map[vid]
                        v["metrics"]["openRate"] = rm.get("openRate", v["metrics"]["openRate"])
                        v["metrics"]["replyRate"] = rm.get("replyRate", v["metrics"]["replyRate"])
                        v["metrics"]["deliveryRate"] = rm.get("deliveryRate", v["metrics"]["deliveryRate"])
        except Exception:
            pass

    return data

@router.get("/{campaign_id}", response_model=Dict[str, Any])
async def get_campaign_analytics(campaign_id: str):
    """Specific campaign variant performance and delivery metrics."""
    return await get_analytics(campaign_id=campaign_id)
