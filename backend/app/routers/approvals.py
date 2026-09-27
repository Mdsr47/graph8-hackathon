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
            # Approved first send: update variants with any human edits and set active
            va = payload.get("variant_a") or {}
            vb = payload.get("variant_b") or {}
            if va.get("id"):
                await db.update_variant(va["id"], status="active", subject=va.get("subject"), body_template=va.get("body_template"))
            if vb.get("id"):
                await db.update_variant(vb["id"], status="active", subject=vb.get("subject"), body_template=vb.get("body_template"))

            # Programmatically launch/sync campaign in Graph8 and dispatch first daily cohort
            camp_id = payload.get("campaign_id")
            if camp_id:
                campaign = (await db.get_campaign(camp_id)) or {}
                # 1. Create campaign in Graph8
                g8_camp = await graph8_client.launch_ab_test_campaign({
                    "id": camp_id,
                    "name": campaign.get("name", "Outbound Campaign"),
                    "variants": [va, vb]
                })

                # 2. Create sequence in Graph8
                g8_seq = await graph8_client.create_sequence(
                    name=f"{campaign.get('name', 'Outbound')} - Sequencer",
                    campaign_id=camp_id
                )
                seq_id = g8_seq.get("id", "seq_auto_01")

                # 3. Add sequence step with Variant copy
                await graph8_client.add_sequence_step(
                    sequence_id=seq_id,
                    step_order=1,
                    subject=va.get("subject", "Quick note on deliverability"),
                    body=va.get("body_template", "")
                )

                from app.services.scheduler_service import scheduler_service
                batch_res = await scheduler_service.process_daily_batch(camp_id, force=False)
                execution_result = {
                    "action": "variants_activated",
                    "status": "active",
                    "graph8_campaign": g8_camp,
                    "graph8_sequence": g8_seq,
                    "batch_dispatch": batch_res
                }
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

    elif req.status == "rejected":
        if app_type == "send_new_variant":
            # 1. Mark rejected variants
            va = payload.get("variant_a") or {}
            vb = payload.get("variant_b") or {}
            if va.get("id"):
                await db.update_variant(va["id"], status="rejected")
            if vb.get("id"):
                await db.update_variant(vb["id"], status="rejected")

            camp_id = payload.get("campaign_id")
            campaign = (await db.get_campaign(camp_id)) or {}
            icp = campaign.get("icp_filters", {})
            selected_ref_ids = campaign.get("reference_email_ids", [])
            all_refs = await db.get_reference_emails()
            ref_emails = [r for r in all_refs if r["id"] in selected_ref_ids] if selected_ref_ids else all_refs[:2]

            # 2. Regenerate fresh contrasting variants incorporating reviewer notes
            rejection_notes = req.notes or "Sharpen value hook, make tone peer-to-peer, eliminate sales friction."
            generated = llm_client.generate_variants(icp, ref_emails, rejection_feedback=rejection_notes)

            new_va_data = generated.get("variant_a", {})
            new_vb_data = generated.get("variant_b", {})

            new_va = await db.create_variant({
                "campaign_id": camp_id,
                "channel": "email",
                "subject": new_va_data.get("subject", "Quick question regarding outbound deliverability at {company}"),
                "body_template": new_va_data.get("body_template", "Hi {name}..."),
                "status": "draft",
                "score": 0.0,
                "allocation_percentage": 50.0
            })

            new_vb = await db.create_variant({
                "campaign_id": camp_id,
                "channel": "email",
                "subject": new_vb_data.get("subject", "3.2x booked meeting rate for {company}"),
                "body_template": new_vb_data.get("body_template", "Hi {name}..."),
                "status": "draft",
                "score": 0.0,
                "allocation_percentage": 50.0
            })

            iteration = payload.get("iteration", 1) + 1
            new_approval = await db.create_approval({
                "type": "send_new_variant",
                "payload": {
                    "campaign_id": camp_id,
                    "variant_a": new_va,
                    "variant_b": new_vb,
                    "strategy": f"Regenerated pair (Iteration #{iteration}) incorporating feedback: '{rejection_notes}'",
                    "reference_templates_used": len(ref_emails),
                    "iteration": iteration,
                    "rejection_reason": rejection_notes
                },
                "status": "pending"
            })

            reg_decision = await db.create_decision({
                "campaign_id": camp_id,
                "decision_type": "regenerate_variants_after_rejection",
                "reasoning": f"Human reviewer rejected initial variants (Feedback: '{rejection_notes}'). Agent generated 2 fresh contrasting variants (Iteration #{iteration}) and placed in Governance Queue.",
                "before_state": {"rejected_variant_ids": [va.get("id"), vb.get("id")]},
                "after_state": {"new_variant_ids": [new_va["id"], new_vb["id"]], "approval_id": new_approval["id"]},
                "requires_approval": True
            })

            await sse_manager.broadcast("agent_decision", reg_decision)
            await sse_manager.broadcast("approval_created", new_approval)
            execution_result = {
                "action": "variants_regenerated",
                "iteration": iteration,
                "new_approval_id": new_approval["id"],
                "status": "pending_human_review"
            }

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
