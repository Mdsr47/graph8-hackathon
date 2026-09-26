from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AgentDecision(BaseModel):
    id: str
    campaign_id: str
    decision_type: str  # reallocate, kill_variant, generate_variant, escalate_voice
    reasoning: str
    before_state: Dict[str, Any] = Field(default_factory=dict)
    after_state: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentDecisionCreate(BaseModel):
    campaign_id: str
    decision_type: str
    reasoning: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
