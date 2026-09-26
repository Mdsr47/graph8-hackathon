from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ICPFilter(BaseModel):
    industry: Optional[str] = "B2B SaaS / Technology"
    target_titles: Optional[List[str]] = Field(default_factory=lambda: ["VP Sales", "Head of Sales", "CRO", "Founder"])
    company_size: Optional[str] = "50-500 employees"
    keywords: Optional[List[str]] = Field(default_factory=lambda: ["sales automation", "outbound", "revenue intelligence"])
    target_domain: Optional[str] = None

class CampaignCreate(BaseModel):
    name: str
    icp_filters: Optional[ICPFilter] = None
    reference_email_ids: Optional[List[str]] = Field(default_factory=list)
    daily_limit: Optional[int] = 50
    target_contacts_limit: int = 50

class Campaign(BaseModel):
    id: str
    name: str
    status: str = "draft"  # draft, active, paused, completed
    icp_filters: Dict[str, Any] = Field(default_factory=dict)
    reference_email_ids: List[str] = Field(default_factory=list)
    daily_limit: int = 50
    sent_today: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    org_id: Optional[str] = None
