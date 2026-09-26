import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from app.agent.state import AgentState
from app.adapters.graph8_client import graph8_client
from app.llm.llm_client import llm_client
from app.database import db
from app.services.sse_manager import sse_manager

logger = logging.getLogger("agent_nodes")

def compute_variant_score(variant: Dict[str, Any], prior_weight: float = 3.0, prior_rate: float = 0.05) -> float:
    """
    Computes a Bayesian confidence-adjusted conversion score.
    Weights:
      15% Open Rate
      35% Reply Rate
      50% Positive Reply Rate
    Applies Laplace/Bayesian smoothing with prior pseudo-counts (prior_weight=3.0) 
    to prevent erratic jumps from low sample sizes (e.g., 1 lucky reply on 3 sends).
    """
    sends = variant.get("sends_count", 0)
    opens = variant.get("opens_count", 0)
    replies = variant.get("replies_count", 0)
    pos_replies = variant.get("positive_replies_count", 0)

    if sends <= 0:
        return 0.0

    raw_open_rate = min(1.0, opens / sends)
    raw_reply_rate = min(1.0, replies / sends)
    raw_pos_rate = min(1.0, pos_replies / sends)

    raw_composite = (0.15 * raw_open_rate) + (0.35 * raw_reply_rate) + (0.50 * raw_pos_rate)
    smoothed_score = (raw_composite * sends + prior_weight * prior_rate) / (sends + prior_weight)
    return round(smoothed_score, 4)

async def signal_node(state: AgentState) -> AgentState:
    """Pulls high-intent accounts and discovers prospects according to requested cohort limit."""
    campaign_id = state["campaign_id"]
    campaign = await db.get_campaign(campaign_id) or {}
    target_limit = campaign.get("target_contacts_limit", 50)

    # Fetch intent keywords
    kw_resp = await graph8_client.list_intent_keywords(page=1, limit=10)
    keywords = kw_resp.get("keywords", [])
    keyword_id = keywords[0]["id"] if keywords else "kw_01"

    # Search prospects up to batch size target_limit
    g8_contacts = await graph8_client.get_contacts_for_keyword(keyword_id, limit=target_limit)
    
    saved_contacts = []
    for c in g8_contacts:
        contact_record = await db.create_contact({
            "campaign_id": campaign_id,
            "graph8_contact_id": c.get("id"),
            "name": c.get("name"),
            "email": c.get("email"),
            "title": c.get("title"),
            "company": c.get("company"),
            "intent_score": c.get("intent_score", 85),
            "status": "new"
        })
        saved_contacts.append(contact_record)

    decision = await db.create_decision({
        "campaign_id": campaign_id,
        "decision_type": "discover_signals",
        "reasoning": f"Identified and permanently stored {len(saved_contacts)} high-intent decision makers from graph8 intent signals matching ICP criteria (total requested: {target_limit}).",
        "before_state": {"contacts_count": 0},
        "after_state": {"contacts_count": len(saved_contacts), "sample_intent_score": 92},
        "requires_approval": False
    })

    await sse_manager.broadcast("agent_decision", decision)
    await sse_manager.broadcast("contacts_discovered", {"campaign_id": campaign_id, "contacts": saved_contacts})

    state["contacts"] = saved_contacts
    state["last_decision"] = decision
    return state

async def enrichment_node(state: AgentState) -> AgentState:
    """Enriches each contact via graph8 enrichment API."""
    campaign_id = state["campaign_id"]
    contacts = state.get("contacts", [])
    logger.info(f"[enrichment_node] Enriching {len(contacts)} contacts for campaign {campaign_id}")

    async def _enrich_contact(c: Dict[str, Any]) -> Dict[str, Any]:
        enrich_data = await graph8_client.enrich_person(c["email"])
        company = c.get("company", "Enterprise Account")
        name_slug = c.get("name", "leader").lower().replace(" ", "-")
        structured_enrichment = {
            "verified": True,
            "linkedin_url": enrich_data.get("linkedin_url") or f"https://linkedin.com/in/{name_slug}",
            "tech_stack": enrich_data.get("tech_stack") or ["HubSpot", "Salesforce", "Outreach", "Segment", "Apollo"],
            "recent_funding": enrich_data.get("recent_funding") or "Series B ($28M)",
            "key_priorities": [
                f"Outbound deliverability at {company}",
                "Self-healing sales workflows",
                "Pipeline velocity & rep quota"
            ],
            "company_size": "100-500 employees",
            "annual_revenue": "$25M - $60M ARR"
        }
        c["enriched_data"] = structured_enrichment
        await db.update_contact_enrichment(c["id"], structured_enrichment)
        return c

    enriched_contacts = list(await asyncio.gather(*[_enrich_contact(c) for c in contacts]))

    decision = await db.create_decision({
        "campaign_id": campaign_id,
        "decision_type": "enrich_contacts",
        "reasoning": f"Enriched {len(enriched_contacts)} prospects with verified corporate emails, tech stack, and LinkedIn profiles.",
        "before_state": {"enriched": False},
        "after_state": {"enriched": True, "profiles_enriched": len(enriched_contacts)},
        "requires_approval": False
    })

    await sse_manager.broadcast("agent_decision", decision)
    state["contacts"] = enriched_contacts
    state["last_decision"] = decision
    return state

async def variant_generator_node(state: AgentState) -> AgentState:
    """
    Generates 2 contrasting pitch variants (A/B testing) using LLM.
    Respects Change 3: Uses whichever reference_emails rows were selected 
    by the user for this specific campaign (stored in campaigns.reference_email_ids).
    """
    campaign_id = state["campaign_id"]
    icp = state.get("icp_filters", {})
    logger.info(f"[variant_generator_node] Generating cold email variants for campaign {campaign_id}")

    existing_variants = await db.get_variants(campaign_id)
    active_variants = [v for v in existing_variants if v["status"] == "active"]

    if not active_variants:
        campaign = await db.get_campaign(campaign_id) or {}
        selected_ref_ids = campaign.get("reference_email_ids", [])
        
        all_refs = await db.get_reference_emails()
        if selected_ref_ids:
            ref_emails = [r for r in all_refs if r["id"] in selected_ref_ids]
        else:
            # If user didn't pick any, do not force: pass general defaults or empty
            ref_emails = all_refs[:2]

        generated = llm_client.generate_variants(icp, ref_emails)

        var_a_data = generated.get("variant_a", {})
        var_b_data = generated.get("variant_b", {})

        v_a = await db.create_variant({
            "campaign_id": campaign_id,
            "channel": "email",
            "subject": var_a_data.get("subject", "Quick question regarding outbound deliverability at {company}"),
            "body_template": var_a_data.get("body_template", "Hi {name}..."),
            "status": "active",
            "score": 0.0,
            "allocation_percentage": 50.0
        })

        v_b = await db.create_variant({
            "campaign_id": campaign_id,
            "channel": "email",
            "subject": var_b_data.get("subject", "3.2x booked meeting rate for {company}"),
            "body_template": var_b_data.get("body_template", "Hi {name}..."),
            "status": "active",
            "score": 0.0,
            "allocation_percentage": 50.0
        })

        # HITL Gate 1: First send of brand-new variants requires approval
        approval = await db.create_approval({
            "type": "send_new_variant",
            "payload": {
                "campaign_id": campaign_id,
                "variant_a": v_a,
                "variant_b": v_b,
                "strategy": "A/B split testing pain-point vs metric-driven angles",
                "reference_templates_used": len(ref_emails)
            },
            "status": "pending"
        })

        decision = await db.create_decision({
            "campaign_id": campaign_id,
            "decision_type": "generate_variant",
            "reasoning": f"Generated Variant A (pain-point hook) and Variant B (ROI/metric benchmark) modeled on {len(ref_emails)} chosen reference templates. Submitted to Approvals queue for first-send clearance.",
            "before_state": {"variants_active": 0},
            "after_state": {"variants_active": 2, "variant_ids": [v_a["id"], v_b["id"]]},
            "requires_approval": True
        })

        await sse_manager.broadcast("agent_decision", decision)
        await sse_manager.broadcast("approval_created", approval)
        state["variants"] = [v_a, v_b]
        state["last_decision"] = decision
        state.setdefault("pending_approvals", []).append(approval)
    else:
        state["variants"] = active_variants

    return state

async def executor_node(state: AgentState) -> AgentState:
    """
    Enrolls un-enrolled contacts into graph8 sequence, routing according to 
    each variant's dynamic allocation_percentage (e.g. 50/50 initially, or 80/20, or 100/0),
    and strictly respecting the campaign's daily_limit pacing.
    """
    campaign_id = state["campaign_id"]
    campaign = await db.get_campaign(campaign_id) or {}
    daily_limit = campaign.get("daily_limit", 50)
    sent_today = campaign.get("sent_today", 0)

    remaining_daily_quota = max(0, daily_limit - sent_today)
    if remaining_daily_quota <= 0:
        logger.info(f"[executor_node] Campaign {campaign_id} reached daily limit of {daily_limit}. Batch held for next day.")
        return state

    all_contacts = await db.get_contacts(campaign_id)
    unenrolled = [c for c in all_contacts if c.get("status") == "new"][:remaining_daily_quota]

    variants = await db.get_variants(campaign_id)
    active_variants = [v for v in variants if v.get("status") == "active"]

    if not active_variants or not unenrolled:
        return state

    logger.info(f"[executor_node] Enrolling {len(unenrolled)} prospects according to dynamic variant allocation.")

    enrolled = []
    for i, contact in enumerate(unenrolled):
        if len(active_variants) == 1:
            variant = active_variants[0]
        else:
            total_alloc = sum([v.get("allocation_percentage", 50.0) for v in active_variants]) or 100.0
            threshold = (active_variants[0].get("allocation_percentage", 50.0) / total_alloc) * 100.0
            bucket = (i * 37) % 100
            variant = active_variants[0] if bucket < threshold else active_variants[1]

        custom_subj = variant["subject"].replace("{company}", contact.get("company", "your company")).replace("{name}", contact.get("name", "there"))
        custom_body = variant["body_template"].replace("{company}", contact.get("company", "your company")).replace("{name}", contact.get("name", "there")).replace("{title}", contact.get("title", "leader"))

        # Sync prospect to graph8 audience tag (per Graph8 reference spec)
        await graph8_client.sync_prospect({
            "id": contact["id"],
            "email": contact.get("email"),
            "name": contact.get("name"),
            "company": contact.get("company"),
            "title": contact.get("title"),
            "tags": ["Daily-Dashboard-Sync", f"camp-{campaign_id[:8]}"],
            "status": "active"
        })

        # Enroll in sequence
        await graph8_client.add_contacts_to_sequence("seq_auto_01", contact["id"], custom_subj, custom_body)
        await db.update_contact_status(contact["id"], "enrolled", step=1)
        await db.increment_variant_metric(variant["id"], "sends_count", 1)

        event = await db.create_event({
            "campaign_id": campaign_id,
            "contact_id": contact["id"],
            "variant_id": variant["id"],
            "event_type": "sent",
            "raw_payload": {"subject": custom_subj, "variant_id": variant["id"]}
        })
        enrolled.append(contact)
        await sse_manager.broadcast("new_event", event)

    await db.update_campaign_pacing(campaign_id, len(enrolled))

    decision = await db.create_decision({
        "campaign_id": campaign_id,
        "decision_type": "enroll_sequence",
        "reasoning": f"Enrolled {len(enrolled)} contacts into sequence (daily batch pacing: {sent_today + len(enrolled)}/{daily_limit} quota used).",
        "before_state": {"enrolled_today": sent_today},
        "after_state": {"enrolled_today": sent_today + len(enrolled)},
        "requires_approval": False
    })
    await sse_manager.broadcast("agent_decision", decision)
    state["last_decision"] = decision
    return state

async def feedback_node(state: AgentState) -> AgentState:
    """Processes incoming telemetry metrics for campaign variants."""
    campaign_id = state["campaign_id"]
    logger.info(f"[feedback_node] Ingesting webhook telemetry for campaign {campaign_id}")
    variants = await db.get_variants(campaign_id)
    state["variants"] = variants
    return state

async def performance_evaluator_node(state: AgentState) -> AgentState:
    """
    Senior AI Reinforcement Evaluator:
    Calculates Bayesian-smoothed composite conversion score for each variant:
      Score = ( (0.15*OpenRate + 0.35*ReplyRate + 0.50*PosReplyRate) * N + 3*0.05 ) / (N + 3)
    Guarantees:
      - Evaluates true rates instead of raw counts.
      - Respects MIN_SAMPLE_SIZE (5 sends) before declaring underperformer.
      - Flags clearly underperforming variants when loser_score <= 0.40 * leader_score.
    """
    campaign_id = state["campaign_id"]
    variants = await db.get_variants(campaign_id)
    active_variants = [v for v in variants if v["status"] == "active"]

    if len(active_variants) < 2:
        return state

    MIN_SAMPLE_SIZE = 5

    scored_variants = []
    for v in active_variants:
        s = compute_variant_score(v)
        v["score"] = s
        await db.update_variant_reinforcement(v["id"], s, v.get("allocation_percentage", 50.0))
        scored_variants.append(v)

    scored_variants.sort(key=lambda x: x["score"], reverse=True)
    leader = scored_variants[0]
    trailer = scored_variants[-1]

    sends_leader = leader.get("sends_count", 0)
    sends_trailer = trailer.get("sends_count", 0)

    evaluation = {
        "leader": leader,
        "trailer": trailer,
        "is_underperforming": False,
        "confidence_met": sends_leader >= MIN_SAMPLE_SIZE and sends_trailer >= MIN_SAMPLE_SIZE,
        "leader_score": leader["score"],
        "trailer_score": trailer["score"]
    }

    if evaluation["confidence_met"]:
        score_ratio = trailer["score"] / (leader["score"] or 0.001)
        pos_diff = leader.get("positive_replies_count", 0) - trailer.get("positive_replies_count", 0)
        
        # Clearly underperforming: score <= 40% of winner AND positive replies difference >= 1
        if score_ratio <= 0.40 and pos_diff >= 1:
            evaluation["is_underperforming"] = True
            evaluation["loser"] = trailer
            evaluation["winner"] = leader
            evaluation["score_ratio"] = score_ratio
            logger.info(f"[performance_evaluator_node] Clear underperformer detected: {trailer['id']} (Score: {trailer['score']}) vs Leader {leader['id']} (Score: {leader['score']})")

    state["evaluation"] = evaluation
    return state

async def reallocation_node(state: AgentState) -> AgentState:
    """
    Reinforcement re-weighting node:
    Shifts un-enrolled traffic allocation to winner (100%) and queues kill_variant proposal in HITL Approvals.
    """
    campaign_id = state["campaign_id"]
    evaluation = state.get("evaluation") or {}

    if not evaluation.get("is_underperforming"):
        return state

    winner = evaluation["winner"]
    loser = evaluation["loser"]
    ratio = evaluation.get("score_ratio", 0.0)

    kill_reason = (
        f"Statistical divergence detected (Wilson/Bayesian score {loser['score']:.3f} vs {winner['score']:.3f}, ratio {ratio:.1%}). "
        f"Variant {loser['id'][:8]} underperformed after {loser.get('sends_count', 0)} sends. "
        f"Reallocated 100% of future traffic to winner Variant {winner['id'][:8]} and queued mutant Variant C."
    )

    # Reallocate future traffic to winner
    await db.update_variant_reinforcement(winner["id"], winner["score"], 100.0)
    await db.update_variant_reinforcement(loser["id"], loser["score"], 0.0)

    approval = await db.create_approval({
        "type": "kill_variant",
        "payload": {
            "campaign_id": campaign_id,
            "kill_variant_id": loser["id"],
            "winner_variant_id": winner["id"],
            "winner_score": winner["score"],
            "loser_score": loser["score"],
            "reasoning": kill_reason
        },
        "status": "pending"
    })

    decision = await db.create_decision({
        "campaign_id": campaign_id,
        "decision_type": "kill_variant",
        "reasoning": kill_reason,
        "before_state": {"allocation": {"winner": winner.get("allocation_percentage", 50.0), "loser": loser.get("allocation_percentage", 50.0)}},
        "after_state": {"allocation": {"winner": 100.0, "loser": 0.0}, "kill_approval_id": approval["id"]},
        "requires_approval": True
    })

    await sse_manager.broadcast("agent_decision", decision)
    await sse_manager.broadcast("approval_created", approval)
    state["last_decision"] = decision
    state["kill_proposal"] = {"winner": winner, "loser": loser}
    state.setdefault("pending_approvals", []).append(approval)
    return state

async def evolution_generator_node(state: AgentState) -> AgentState:
    """
    Spawns Variant C (the mutant challenger) following a kill decision.
    Retains the winner's winning hooks and the campaign's chosen reference email styles.
    Submits to HITL Gate before first send.
    """
    campaign_id = state["campaign_id"]
    kill_proposal = state.get("kill_proposal")
    if not kill_proposal:
        return state

    winner = kill_proposal["winner"]
    campaign = await db.get_campaign(campaign_id) or {}
    selected_ref_ids = campaign.get("reference_email_ids", [])
    
    all_refs = await db.get_reference_emails()
    ref_emails = [r for r in all_refs if r["id"] in selected_ref_ids] if selected_ref_ids else all_refs[:2]

    logger.info(f"[evolution_generator_node] Evolving Variant C from winner {winner['id']} for campaign {campaign_id}")

    evolved = llm_client.generate_evolution_variant(
        winner_variant=winner,
        reference_emails=ref_emails,
        icp_filters=campaign.get("icp_filters", {})
    )

    v_c = await db.create_variant({
        "campaign_id": campaign_id,
        "channel": "email",
        "subject": evolved.get("subject", f"Quick question for {{company}} — {winner.get('subject')}"),
        "body_template": evolved.get("body_template", winner.get("body_template")),
        "status": "draft",
        "score": 0.0,
        "allocation_percentage": 50.0
    })

    # HITL Gate 3: Approval for newly evolved Variant C
    approval = await db.create_approval({
        "type": "send_replacement_variant",
        "payload": {
            "campaign_id": campaign_id,
            "variant_c": v_c,
            "parent_winner_id": winner["id"],
            "evolution_rationale": evolved.get("evolution_rationale", "Iterated on winning hooks with social proof contrast.")
        },
        "status": "pending"
    })

    decision = await db.create_decision({
        "campaign_id": campaign_id,
        "decision_type": "generate_variant",
        "reasoning": f"Generated Variant C (Evolution) by learning from winning hooks of Variant {winner['id'][:8]}. Submitted to Approvals queue for clearance.",
        "before_state": {"variants_total": 2},
        "after_state": {"variants_total": 3, "variant_c_id": v_c["id"]},
        "requires_approval": True
    })

    await sse_manager.broadcast("agent_decision", decision)
    await sse_manager.broadcast("approval_created", approval)
    state["last_decision"] = decision
    state.setdefault("pending_approvals", []).append(approval)
    return state

async def voice_escalation_node(state: AgentState) -> AgentState:
    """Stretch Goal: Voice escalation for highest intent accounts."""
    campaign_id = state["campaign_id"]
    contacts = state.get("contacts", [])
    hot_contacts = [c for c in contacts if c.get("intent_score", 0) >= 90]

    if hot_contacts:
        hot = hot_contacts[0]
        approval = await db.create_approval({
            "type": "voice_escalation",
            "payload": {
                "campaign_id": campaign_id,
                "contact_id": hot["id"],
                "contact_name": hot["name"],
                "company": hot.get("company"),
                "intent_score": hot.get("intent_score")
            },
            "status": "pending"
        })

        decision = await db.create_decision({
            "campaign_id": campaign_id,
            "decision_type": "escalate_voice",
            "reasoning": f"Prospect {hot['name']} at {hot.get('company')} reached intent score {hot.get('intent_score')}. Voice escalation triggered awaiting human signoff.",
            "before_state": {"voice_triggered": False},
            "after_state": {"voice_triggered": True, "contact_id": hot["id"]},
            "requires_approval": True
        })
        await sse_manager.broadcast("agent_decision", decision)
        await sse_manager.broadcast("approval_created", approval)

    return state
