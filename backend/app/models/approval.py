from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Approval(BaseModel):
    id: str
    decision_id: Optional[str] = None
    type: str  # send_new_variant, kill_variant, voice_escalation, reply_draft
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

class ApprovalResolveRequest(BaseModel):
    status: str  # approved, rejected
    notes: Optional[str] = None
    edited_payload: Optional[Dict[str, Any]] = None
