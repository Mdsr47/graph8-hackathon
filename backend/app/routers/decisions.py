from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from app.database import db

router = APIRouter(prefix="/api/decisions", tags=["decisions"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_decisions(campaign_id: Optional[str] = Query(None), limit: int = Query(50)):
    return await db.get_decisions(campaign_id=campaign_id, limit=limit)
