from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict

class AgentState(TypedDict):
    campaign_id: str
    segment: str
    icp_filters: Dict[str, Any]
    contacts: List[Dict[str, Any]]
    variants: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    last_decision: Optional[Dict[str, Any]]
    pending_approvals: List[Dict[str, Any]]
    cycle_count: int
    status: str
