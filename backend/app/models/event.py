from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Event(BaseModel):
    id: str
    contact_id: Optional[str] = None
    variant_id: Optional[str] = None
    event_type: str  # sent, opened, replied, bounced, meeting_booked
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    sentiment: Optional[str] = None  # positive, neutral, negative
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EventCreate(BaseModel):
    contact_id: Optional[str] = None
    variant_id: Optional[str] = None
    event_type: str
    raw_payload: Optional[Dict[str, Any]] = None
    sentiment: Optional[str] = None
