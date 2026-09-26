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
    reallocation_node,
    voice_escalation_node
)

logger = logging.getLogger("workflow")

def build_workflow():
    """
    Constructs the LangGraph cyclical StateGraph.
    Contains a real cyclical edge back from reallocation to feedback or variant generation.
    """
    builder = StateGraph(AgentState)

    # 1. Add Nodes
    builder.add_node("signal_node", signal_node)
    builder.add_node("enrichment_node", enrichment_node)
    builder.add_node("variant_generator_node", variant_generator_node)
    builder.add_node("executor_node", executor_node)
    builder.add_node("feedback_node", feedback_node)
    builder.add_node("reallocation_node", reallocation_node)
    builder.add_node("voice_escalation_node", voice_escalation_node)

    # 2. Linear Initial Discovery Flow
    builder.set_entry_point("signal_node")
    builder.add_edge("signal_node", "enrichment_node")
    builder.add_edge("enrichment_node", "variant_generator_node")
    builder.add_edge("variant_generator_node", "executor_node")

    # 3. Cyclical Edge Routing
    def route_after_executor(state: AgentState):
        # Once sequence executed, wait for webhooks / go to feedback
        return "feedback_node"

    builder.add_conditional_edges("executor_node", route_after_executor, {
        "feedback_node": "feedback_node"
    })

    builder.add_edge("feedback_node", "reallocation_node")

    def route_after_reallocation(state: AgentState):
        decision = state.get("last_decision") or {}
        dtype = decision.get("decision_type")

        # If a variant was killed, generate a new variant (Closing the Reinforcement Loop!)
        if dtype == "kill_variant":
            return "variant_generator_node"
        elif dtype == "escalate_voice":
            return "voice_escalation_node"
        
        # Otherwise end cycle and wait for next webhook batch
        return END

    # Cyclical edge: reallocation can loop back to variant_generator_node or voice_escalation_node
    builder.add_conditional_edges("reallocation_node", route_after_reallocation, {
        "variant_generator_node": "variant_generator_node",
        "voice_escalation_node": "voice_escalation_node",
        END: END
    })

    builder.add_edge("voice_escalation_node", END)

    # Checkpointing memory store
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
    """Re-enters the LangGraph workflow directly at feedback_node upon incoming webhook event."""
    config = {"configurable": {"thread_id": campaign_id}}
    
    # Update state with incoming event and trigger feedback & reallocation
    state_update = {
        "campaign_id": campaign_id,
        "events": [event_data]
    }
    logger.info(f"[Workflow] Re-entering cyclical workflow at feedback_node for campaign {campaign_id}")
    
    # Run feedback node directly
    result = await feedback_node(state_update)
    final_result = await reallocation_node(result)
    return final_result
