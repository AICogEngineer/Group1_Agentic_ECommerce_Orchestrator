"""
agent.py

Primary orchestration file for the Agentic E-Commerce Orchestrator.

Responsibilities:
- Load environment variables (PII / credentials live in .env)
- Define and compile the LangGraph workflow
- Expose a single run_agent() entry point
- Enforce HITL and fraud gating at the graph level
"""

# Environment & Imports
import os
from dotenv import load_dotenv
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

# Agent state and routing logic
from agent.state import AgentState # AgentState (Pydantic / TypedDict)
from agent.router import route_next_step # Routing decisions

# Node implementations
    # Internal project modules (no pip-install for the following)
from nodes.verify_identity import verify_identity_node # HITL security gate
from nodes.retrieve_data import retrieve_data_node # Snowflake + Pinecone reasoning
from nodes.red_flag_checker import red_flag_checker_node # Fraud detection logic
from nodes.risk_scoring import risk_scoring_node # Trust score
from nodes.human_review import human_review_node # Human approval step
from nodes.draft_response import draft_response_node # Response/email drafting


# Environment Setup
# Load credentials and PII-related config in the .env (Snowflake creds, Pinecone API key, policy thresholds)
load_dotenv()

# Graph Definition
def build_agent_graph() -> StateGraph:
    """
    Builds the agentic workflow as a stateful, auditable graph.

    Workflow enforces:
    - Mandatory identity verification (HITL)
    - Multi-source reasoning (Snowflake + Pinecone)
    - Fraud / red-flag detection
    - Human review for high-risk actions
    """

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("verify_identity", verify_identity_node)
    graph.add_node("retrieve_data", retrieve_data_node)
    graph.add_node("red_flag_check", red_flag_checker_node)
    graph.add_node("risk_scoring", risk_scoring_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("draft_response", draft_response_node)

    # Entry Point
    graph.add_edge(START, "verify_identity") # Every sensitive request must pass identity verification first

    # Conditional routing based on node outputs
    graph.add_conditional_edges(
        "verify_identity",
        route_next_step,
        {
            "blocked": END,              # Identity not verified
            "continue": "retrieve_data"  # Verified, safe to reason
        }
    )

    graph.add_edge("retrieve_data", "red_flag_check")

    graph.add_conditional_edges(
        "red_flag_check",
        route_next_step,
        {
            "human_review": "human_review",
            "auto_approve": "risk_scoring"
        }
    )

    graph.add_conditional_edges(
        "risk_scoring",
        route_next_step,
        {
            "human_review": "human_review",
            "draft": "draft_response"
        }
    )

    graph.add_conditional_edges(
        "human_review",
        route_next_step,
        {
            "approved": "draft_response",
            "rejected": END
        }
    )

    graph.add_edge("draft_response", END)

    return graph

# Agent Runtime
def run_agent(user_input: str, session_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the agent for a single user interaction.

    Args:
        user_input: Raw user request (ex: refund request)
        session_metadata: Session / login context used for fraud checks

    Returns:
        Final agent state (safe to log / inspect)
    """

    # Initialize the agent state
    initial_state = AgentState(
        user_input = user_input,
        session_metadata = session_metadata,

        # Identity / control
        is_verified = False,
        requires_human_review = False,
        status = None,

        # Fraud / risk
        refund_count = session_metadata.get("refund_count", 0),
        address_drift_miles = session_metadata.get("address_drift_miles", 0.0),
        red_flags = [],

        # HITL
        human_decision = None
    )

    # Build and compile the workflow graph
    graph = build_agent_graph().compile()

    # Execute the workflow
    final_state = graph.invoke(initial_state)

    return final_state.dict()


# Local Demo
if __name__ == "__main__":
    demo_input = "Show my last order" # Example user request, should triggers identity check

    demo_session = {
        "user_id": "demo_user_123",  # PII from .env
        "email": "user@example.com",  # PII from .env
        "ip_address": "73.15.182.91", # Example public IP
        "geo_location": "TX",
        "device_id": "demo-device",
        "refund_count": 0,
        "address_drift_miles": 0
    }

    output = run_agent(demo_input, demo_session)

    print("Final agent state:")
    print(output)

    # Safety assertion: agent must halt at identity verification if PII missing
    assert output.get("status") in {
        "IDENTITY_REQUIRED",
        "IDENTITY_FAILED",
        "IDENTITY_VERIFIED" # passes if correct demo PII provided
    }
