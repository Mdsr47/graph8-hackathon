from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional, Union
import math
from app.database import db
from app.adapters.graph8_client import graph8_client

router = APIRouter(prefix="/api/prospects", tags=["prospects"])

@router.get("")
async def get_prospects(
    campaign_id: Optional[str] = Query(None),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """
    Returns list of prospects.
    If page and page_size are supplied, returns a paginated structure with total, page, total_pages, and items.
    If omitted, returns flat list for seamless backwards compatibility.
    """
    if page is not None:
        p_size = page_size or 20
        offset = (page - 1) * p_size
        items = await db.get_contacts(campaign_id=campaign_id, limit=p_size, offset=offset, search=search, status=status)
        total = await db.count_contacts(campaign_id=campaign_id, search=search, status=status)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": p_size,
            "total_pages": math.ceil(total / p_size) if total > 0 else 1
        }

    return await db.get_contacts(campaign_id=campaign_id, search=search, status=status)

@router.get("/{contact_id}/signals")
async def get_prospect_signals(contact_id: str):
    signals = await graph8_client.get_contact_signals(contact_id)
    return signals
