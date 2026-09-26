from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MailboxStatusModel(BaseModel):
    id: str
    provider: str = "gmail"  # gmail, outlook, smtp
    graph8_mailbox_id: Optional[str] = None
    connected_at: Optional[datetime] = None
    status: str = "active"  # active, warming_up, error, disconnected

class ReferenceEmail(BaseModel):
    id: str
    subject: str
    body: str
    style_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReferenceEmailCreate(BaseModel):
    subject: str
    body: str
    style_notes: Optional[str] = None
