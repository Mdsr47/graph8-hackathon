from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.database import db
from app.models.approval import ApprovalResolveRequest
from app.adapters.graph8_client import graph8_client
from app.llm.llm_client import llm_client
from app.services.sse_manager import sse_manager

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_approvals(status: Optional[str] = Query(None)):
    return await db.get_approvals(status)

@router.post("/{approval_id}/resolve")
async def resolve_approval(approval_id: str, req: ApprovalResolveRequest):
    approvals = await db.get_approvals()
    matched = [a for a in approvals if a["id"] == approval_id]
    if not matched:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval = matched[0]
    app_type = approval["type"]
    payload = req.edited_payload if req.edited_payload is not None else approval["payload"]

    await db.resolve_approval(approval_id, req.status, edited_payload=payload)

    # If approved, execute the gated action
    execution_result = {}
    if req.status == "approved":
        if app_type == "send_new_variant":
            # Approved first send: enroll sequence
            execution_result = {"action": "variants_activated", "status": "active"}

        elif app_type == "kill_variant":
            kill_vid = payload.get("kill_variant_id")
            campaign_id = payload.get("campaign_id")
            if kill_vid:
                await db.kill_variant(kill_vid)

            # Auto-generate replacement Variant C
            if campaign_id:
                ref_emails = await db.get_reference_emails()
                gen = llm_client.generate_variants({"industry": "B2B SaaS"}, ref_emails)
                v_c_data = gen.get("variant_b", {})
                new_var = await db.create_variant({
                    "campaign_id": campaign_id,
                    "channel": "email",
                    "subject": v_c_data.get("subject", "Evolving our outbound strategy for {company}"),
                    "body_template": v_c_data.get("body_template", "Hi {name}..."),
                    "status": "active"
                })
                execution_result = {"killed_variant_id": kill_vid, "new_variant_generated": new_var}

        elif app_type == "reply_draft":
            item_id = payload.get("inbox_item_id")
            draft_text = payload.get("draft_body")
            if item_id and draft_text:
                resp = await graph8_client.send_reply(item_id, draft_text)
                await graph8_client.tag_reply(item_id, "replied")
                execution_result = {"inbox_reply_sent": True, "graph8_resp": resp}

        elif app_type == "voice_escalation":
            contact_id = payload.get("contact_id")
            if contact_id:
                resp = await graph8_client.trigger_voice_call(contact_id, payload)
                execution_result = {"voice_call_initiated": True, "graph8_resp": resp}

    # Record decision audit
    decision = await db.create_decision({
        "campaign_id": payload.get("campaign_id", "00000000-0000-0000-0000-000000000000"),
        "decision_type": f"hitl_approval_{req.status}",
        "reasoning": f"Human user {req.status} {app_type} gate. Notes: {req.notes or 'None'}",
        "before_state": {"approval_id": approval_id, "type": app_type},
        "after_state": {"status": req.status, "execution": execution_result},
        "requires_approval": False
    })

    await sse_manager.broadcast("agent_decision", decision)
    await sse_manager.broadcast("approval_resolved", {"id": approval_id, "status": req.status})

    return {
        "id": approval_id,
        "status": req.status,
        "execution_result": execution_result
    }
