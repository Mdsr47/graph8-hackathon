from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.database import db
from app.adapters.graph8_client import graph8_client

router = APIRouter(prefix="/api/prospects", tags=["prospects"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_prospects(campaign_id: Optional[str] = Query(None)):
    contacts = await db.get_contacts(campaign_id)
    return contacts

@router.get("/{contact_id}/signals")
async def get_prospect_signals(contact_id: str):
    signals = await graph8_client.get_contact_signals(contact_id)
    return signals
