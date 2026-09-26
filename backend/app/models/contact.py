from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Contact(BaseModel):
    id: str
    campaign_id: str
    graph8_contact_id: Optional[str] = None
    name: str
    email: str
    title: Optional[str] = None
    company: Optional[str] = None
    intent_score: int = 0
    current_step: int = 1
    status: str = "new"  # new, enrolled, replied, bounced, meeting_booked
    enriched_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ContactCreate(BaseModel):
    campaign_id: str
    name: str
    email: str
    title: Optional[str] = None
    company: Optional[str] = None
    intent_score: int = 0
    enriched_data: Optional[Dict[str, Any]] = None
