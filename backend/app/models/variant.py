from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Variant(BaseModel):
    id: str
    campaign_id: str
    channel: str = "email"
    subject: str
    body_template: str
    status: str = "active"  # active, killed, draft
    sends_count: int = 0
    opens_count: int = 0
    replies_count: int = 0
    positive_replies_count: int = 0
    meetings_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    killed_at: Optional[datetime] = None

class VariantCreate(BaseModel):
    campaign_id: str
    channel: str = "email"
    subject: str
    body_template: str
    status: str = "active"
