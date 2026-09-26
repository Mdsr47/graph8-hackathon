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
            # Approved first send: update variants with any human edits
            va = payload.get("variant_a") or {}
            vb = payload.get("variant_b") or {}
            if va.get("id"):
                await db.update_variant(va["id"], subject=va.get("subject"), body_template=va.get("body_template"))
            if vb.get("id"):
                await db.update_variant(vb["id"], subject=vb.get("subject"), body_template=vb.get("body_template"))

            # Dispatch first daily cohort into sequence
            camp_id = payload.get("campaign_id")
            if camp_id:
                from app.services.scheduler_service import scheduler_service
                batch_res = await scheduler_service.process_daily_batch(camp_id)
                execution_result = {"action": "variants_activated", "status": "active", "batch_dispatch": batch_res}
            else:
                execution_result = {"action": "variants_activated", "status": "active"}

        elif app_type == "kill_variant":
            kill_vid = payload.get("kill_variant_id")
            if kill_vid:
                await db.kill_variant(kill_vid)
            execution_result = {"killed_variant_id": kill_vid, "status": "killed"}

        elif app_type == "send_replacement_variant":
            variant_c = payload.get("variant_c") or {}
            vid = variant_c.get("id")
            if vid:
                updated_subj = payload.get("subject") or variant_c.get("subject")
                updated_body = payload.get("body_template") or variant_c.get("body_template")
                await db.update_variant(vid, status="active", subject=updated_subj, body_template=updated_body, allocation_percentage=50.0)
                # Split allocation 50/50 with parent winner
                winner_id = payload.get("parent_winner_id")
                if winner_id:
                    winner = await db.get_variant(winner_id)
                    if winner:
                        await db.update_variant_reinforcement(winner_id, winner.get("score", 0.0), 50.0)
                execution_result = {"variant_c_activated": vid, "status": "active", "allocation_split": "50/50"}

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
