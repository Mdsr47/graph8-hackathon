import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agent.state import AgentState
from app.agent.nodes import (
    signal_node,
    enrichment_node,
    variant_generator_node,
    executor_node,
    feedback_node,
    performance_evaluator_node,
    reallocation_node,
    evolution_generator_node,
    voice_escalation_node
)

logger = logging.getLogger("workflow")

def build_workflow():
    """
    Constructs the LangGraph cyclical StateGraph.
    Designed by Senior AI Engineer with Bayesian scoring, dynamic reallocation,
    and sequential evolution generation.
    """
    builder = StateGraph(AgentState)

    # 1. Add Modular Nodes
    builder.add_node("signal_node", signal_node)
    builder.add_node("enrichment_node", enrichment_node)
    builder.add_node("variant_generator_node", variant_generator_node)
    builder.add_node("executor_node", executor_node)
    builder.add_node("feedback_node", feedback_node)
    builder.add_node("performance_evaluator_node", performance_evaluator_node)
    builder.add_node("reallocation_node", reallocation_node)
    builder.add_node("evolution_generator_node", evolution_generator_node)
    builder.add_node("voice_escalation_node", voice_escalation_node)

    # 2. Linear Initial Discovery Flow
    builder.set_entry_point("signal_node")
    builder.add_edge("signal_node", "enrichment_node")
    builder.add_edge("enrichment_node", "variant_generator_node")
    builder.add_edge("variant_generator_node", "executor_node")
    builder.add_edge("executor_node", END)

    # 3. Cyclical Feedback & Reallocation Graph
    builder.add_edge("feedback_node", "performance_evaluator_node")
    builder.add_edge("performance_evaluator_node", "reallocation_node")

    def route_after_reallocation(state: AgentState):
        if state.get("kill_proposal"):
            return "evolution_generator_node"
        
        # Check if high intent triggers voice escalation
        events = state.get("events", [])
        if any(e.get("intent_score", 0) >= 90 or "voice" in str(e.get("event_type", "")) for e in events):
            return "voice_escalation_node"

        return END

    builder.add_conditional_edges("reallocation_node", route_after_reallocation, {
        "evolution_generator_node": "evolution_generator_node",
        "voice_escalation_node": "voice_escalation_node",
        END: END
    })

    builder.add_edge("evolution_generator_node", END)
    builder.add_edge("voice_escalation_node", END)

    checkpointer = MemorySaver()
    app = builder.compile(checkpointer=checkpointer)
    return app

workflow_engine = build_workflow()

async def run_campaign_initiation(campaign_id: str, icp_filters: Dict[str, Any]):
    """Initializes and runs the initial discovery and generation pipeline for a campaign."""
    initial_state: AgentState = {
        "campaign_id": campaign_id,
        "segment": icp_filters.get("industry", "Default"),
        "icp_filters": icp_filters,
        "contacts": [],
        "variants": [],
        "events": [],
        "last_decision": None,
        "pending_approvals": [],
        "cycle_count": 1,
        "status": "active"
    }

    config = {"configurable": {"thread_id": campaign_id}}
    result = await workflow_engine.ainvoke(initial_state, config=config)
    return result

async def trigger_feedback_cycle(campaign_id: str, event_data: Dict[str, Any]):
    """
    Re-enters the LangGraph workflow directly at feedback_node upon incoming webhook event.
    Evaluates Bayesian confidence scores, executes dynamic reallocation if an underperformer
    is detected, and spawns Variant C via evolution_generator_node.
    """
    logger.info(f"[Workflow] Re-entering cyclical workflow at feedback_node for campaign {campaign_id}")
    state_update: AgentState = {
        "campaign_id": campaign_id,
        "events": [event_data]
    }
    
    # 1. Ingest telemetry
    s1 = await feedback_node(state_update)
    # 2. Senior AI Bayesian scoring & evaluation
    s2 = await performance_evaluator_node(s1)
    # 3. Dynamic reallocation & kill proposal
    s3 = await reallocation_node(s2)
    # 4. Sequential evolution: generate Variant C if underperformer killed
    if s3.get("kill_proposal"):
        s4 = await evolution_generator_node(s3)
        return s4
    return s3
