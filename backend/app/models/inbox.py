from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class InboxItem(BaseModel):
    id: str
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    company: Optional[str] = None
    subject: str
    body: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    sentiment: str = "neutral"  # positive, neutral, negative
    status: str = "unhandled"   # unhandled, replied, archived
    ai_draft_reply: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class ReplySendRequest(BaseModel):
    reply_id: str
    text: str
