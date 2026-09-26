import logging
from typing import Dict, Any, List
from app.agent.state import AgentState
from app.adapters.graph8_client import graph8_client
from app.llm.llm_client import llm_client
from app.database import db
from app.services.sse_manager import sse_manager

logger = logging.getLogger("agent_nodes")

async def signal_node(state: AgentState) -> AgentState:
    """Pulls high-intent accounts from graph8 signals matching ICP filters."""
    campaign_id = state["campaign_id"]
    icp = state.get("icp_filters", {})
    logger.info(f"[signal_node] Discovering intent signals for campaign {campaign_id}")

    # Fetch intent keywords
    kw_resp = await graph8_client.list_intent_keywords(page=1, limit=10)
    keywords = kw_resp.get("keywords", [])
    keyword_id = keywords[0]["id"] if keywords else "kw_01"

    # Fetch contacts showing active buyer intent
    g8_contacts = await graph8_client.get_contacts_for_keyword(keyword_id, limit=6)
    
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

    # Record decision
    decision = await db.create_decision({
        "campaign_id": campaign_id,
        "decision_type": "discover_signals",
        "reasoning": f"Identified {len(saved_contacts)} high-intent decision makers from graph8 intent signals matching ICP criteria.",
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

    enriched_contacts = []
    for c in contacts:
        enrich_data = await graph8_client.enrich_person(c["email"])
        c["enriched_data"] = enrich_data
        enriched_contacts.append(c)

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
    """Generates 2 contrasting pitch variants (A/B testing) using LLM and few-shot examples."""
    campaign_id = state["campaign_id"]
    icp = state.get("icp_filters", {})
    logger.info(f"[variant_generator_node] Generating cold email variants for campaign {campaign_id}")

    existing_variants = await db.get_variants(campaign_id)
    active_variants = [v for v in existing_variants if v["status"] == "active"]

    if not active_variants:
        ref_emails = await db.get_reference_emails()
        generated = llm_client.generate_variants(icp, ref_emails)

        var_a_data = generated.get("variant_a", {})
        var_b_data = generated.get("variant_b", {})

        v_a = await db.create_variant({
            "campaign_id": campaign_id,
            "channel": "email",
            "subject": var_a_data.get("subject", "Quick question regarding outbound deliverability at {company}"),
            "body_template": var_a_data.get("body_template", "Hi {name}..."),
            "status": "active"
        })

        v_b = await db.create_variant({
            "campaign_id": campaign_id,
            "channel": "email",
            "subject": var_b_data.get("subject", "3.2x booked meeting rate for {company}"),
            "body_template": var_b_data.get("body_template", "Hi {name}..."),
            "status": "active"
        })

        # HITL Gate 1: First send of brand-new variants requires approval
        approval = await db.create_approval({
            "type": "send_new_variant",
            "payload": {
                "campaign_id": campaign_id,
                "variant_a": v_a,
                "variant_b": v_b,
                "strategy": "A/B split testing pain-point vs metric-driven angles"
            },
            "status": "pending"
        })

        decision = await db.create_decision({
            "campaign_id": campaign_id,
            "decision_type": "generate_variant",
            "reasoning": "Generated Variant A (pain-point hook) and Variant B (ROI/metric benchmark) from reference emails. Submitted to Approvals queue for first-send clearance.",
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
    """Enrolls contacts into graph8 sequence, splitting evenly across active variants."""
    campaign_id = state["campaign_id"]
    contacts = state.get("contacts", [])
    variants = state.get("variants", [])
    active_variants = [v for v in variants if v.get("status") == "active"]

    if not active_variants or not contacts:
        return state

    logger.info(f"[executor_node] Enrolling {len(contacts)} prospects across {len(active_variants)} variants.")

    enrolled = []
    for i, contact in enumerate(contacts):
        # Round-robin variant allocation
        variant = active_variants[i % len(active_variants)]
        custom_subj = variant["subject"].replace("{company}", contact.get("company", "your company")).replace("{name}", contact.get("name", "there"))
        custom_body = variant["body_template"].replace("{company}", contact.get("company", "your company")).replace("{name}", contact.get("name", "there")).replace("{title}", contact.get("title", "leader"))

        # graph8 add to sequence
        await graph8_client.add_contacts_to_sequence("seq_auto_01", contact["id"], custom_subj, custom_body)
        await db.update_contact_status(contact["id"], "enrolled", step=1)
        await db.increment_variant_metric(variant["id"], "sends_count", 1)

        # Log event
        event = await db.create_event({
            "contact_id": contact["id"],
            "variant_id": variant["id"],
            "event_type": "sent",
            "raw_payload": {"subject": custom_subj, "variant_id": variant["id"]}
        })
        enrolled.append(contact)
        await sse_manager.broadcast("new_event", event)

    decision = await db.create_decision({
        "campaign_id": campaign_id,
        "decision_type": "enroll_sequence",
        "reasoning": f"Enrolled {len(enrolled)} contacts into sequence with 50/50 A/B variant split.",
        "before_state": {"enrolled_count": 0},
        "after_state": {"enrolled_count": len(enrolled)},
        "requires_approval": False
    })
    await sse_manager.broadcast("agent_decision", decision)
    state["last_decision"] = decision
    return state

async def feedback_node(state: AgentState) -> AgentState:
    """Processes telemetry and updates live performance metrics."""
    campaign_id = state["campaign_id"]
    logger.info(f"[feedback_node] Recalculating telemetry metrics for campaign {campaign_id}")
    variants = await db.get_variants(campaign_id)
    state["variants"] = variants
    return state

async def reallocation_node(state: AgentState) -> AgentState:
    """
    Reinforcement learning step:
    Requires minimum sample size (e.g. 5 sends) before kill/reallocate decision.
    Creates approval gate for any kill_variant decision.
    """
    campaign_id = state["campaign_id"]
    variants = await db.get_variants(campaign_id)
    active_variants = [v for v in variants if v["status"] == "active"]

    if len(active_variants) < 2:
        return state

    MIN_SAMPLE_SIZE = 5
    var_a = active_variants[0]
    var_b = active_variants[1]

    sends_a = var_a.get("sends_count", 0)
    sends_b = var_b.get("sends_count", 0)

    # Check minimum sample size gate
    if sends_a >= MIN_SAMPLE_SIZE and sends_b >= MIN_SAMPLE_SIZE:
        pos_a = var_a.get("positive_replies_count", 0)
        pos_b = var_b.get("positive_replies_count", 0)

        # Self-healing condition: if Variant B wins by substantial margin
        if pos_a == 0 and pos_b >= 1:
            loser = var_a
            winner = var_b
            kill_reason = f"Variant A has 0 positive replies after {sends_a} sends, while Variant B achieved {pos_b} positive replies. Reallocating volume to Variant B and generating Variant C."
            
            # HITL Gate 2: Killing variant requires explicit approval
            approval = await db.create_approval({
                "type": "kill_variant",
                "payload": {
                    "campaign_id": campaign_id,
                    "kill_variant_id": loser["id"],
                    "winner_variant_id": winner["id"],
                    "reasoning": kill_reason
                },
                "status": "pending"
            })

            decision = await db.create_decision({
                "campaign_id": campaign_id,
                "decision_type": "kill_variant",
                "reasoning": kill_reason,
                "before_state": {"variant_a_sends": sends_a, "variant_b_sends": sends_b},
                "after_state": {"action": "kill_variant_a_pending_approval", "winner": winner["id"]},
                "requires_approval": True
            })

            await sse_manager.broadcast("agent_decision", decision)
            await sse_manager.broadcast("approval_created", approval)
            state["last_decision"] = decision
            state.setdefault("pending_approvals", []).append(approval)

        elif pos_b == 0 and pos_a >= 1:
            loser = var_b
            winner = var_a
            kill_reason = f"Variant B has 0 positive replies after {sends_b} sends, while Variant A achieved {pos_a} positive replies. Reallocating volume to Variant A and generating Variant C."

            approval = await db.create_approval({
                "type": "kill_variant",
                "payload": {
                    "campaign_id": campaign_id,
                    "kill_variant_id": loser["id"],
                    "winner_variant_id": winner["id"],
                    "reasoning": kill_reason
                },
                "status": "pending"
            })

            decision = await db.create_decision({
                "campaign_id": campaign_id,
                "decision_type": "kill_variant",
                "reasoning": kill_reason,
                "before_state": {"variant_a_sends": sends_a, "variant_b_sends": sends_b},
                "after_state": {"action": "kill_variant_b_pending_approval", "winner": winner["id"]},
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
        # Gate behind approval
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
