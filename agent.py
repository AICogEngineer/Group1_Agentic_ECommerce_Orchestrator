"""
agent.py

Primary orchestration file for the Agentic E-Commerce Orchestrator.

Responsibilities:
- Load environment variables (PII / credentials live in .env)
- Define and compile the LangGraph workflow
- Expose a single run_agent() entry point
- Enforce HITL and fraud gating at the graph level
- Integrate with LangSmith for traceability
"""

# Environment & Imports
import os
from dotenv import load_dotenv
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END
from langsmith import Client

from agent.state import AgentState, AgentStatus, FraudSignals, Intent
from agent.router import route_next_step

# Nodes
from nodes.verify_identity import verify_identity_node
from nodes.retrieve_data import retrieve_data_node
from nodes.red_flag_checker import red_flag_checker_node
from nodes.risk_scoring import risk_scoring_node
from nodes.human_review import human_review_node
from nodes.draft_response import draft_response_node

# Environment Setup
load_dotenv()  # Load .env credentials (USER_ID, USER_EMAIL, Snowflake/Pinecone credentials, etc.)

# Graph Definition
def build_agent_graph() -> StateGraph:
    """
    Builds the LangGraph workflow.

    The graph enforces:
    - Mandatory identity verification (HITL)
    - Multi-source reasoning (Snowflake + Pinecone)
    - Fraud / red-flag detection
    - Human approval for high-risk actions
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
    graph.add_edge(START, "verify_identity")

    # Identity Gate
    graph.add_conditional_edges(
        "verify_identity",
        route_next_step,
        {
            "blocked": END,
            "continue": "retrieve_data",
        },
    )

    # Retrieval -> Flags
    graph.add_edge("retrieve_data", "red_flag_check")
    
    # Flags Gate
    graph.add_conditional_edges(
        "red_flag_check",
        route_next_step,
        {
            "human_review": "human_review",
            "continue": "risk_scoring",
        },
    )

    # Risk Scoring Gate
    graph.add_conditional_edges(
        "risk_scoring",
        route_next_step,
        {
            "human_review": "human_review",
            "continue": "draft_response",
        },
    )

    # Human Review Outcomes
    graph.add_conditional_edges(
        "human_review",
        route_next_step,
        {
            "approved": "draft_response",
            "rejected": END,
        },
    )

    # Final 
    graph.add_edge("draft_response", END)

    return graph

# Agent Runtime
def run_agent(user_input: str, session_metadata: Dict[str, Any]) -> AgentState:
    """
    Executes the agent for a single user interaction.

    Args:
        user_input: Raw user request (ex: "Show my last order")
        session_metadata: Session / login context used for fraud checks

    Returns:
        AgentState object (fully typed, ready to log or inspect)
    """

    # Initialize AgentState with required fields, including FraudSignals
    initial_state = AgentState(
        user_input = user_input,
        session_metadata = session_metadata,

        # Intent is refined later
        intent = Intent.OTHER,

        # Identity
        is_verified = False,
        contains_pii = False,
        status = AgentStatus.IDENTITY_REQUIRED,  # start lifecycle

        # Fraud primitives
        refund_count = session_metadata.get("refund_count", 0),
        address_drift_miles = session_metadata.get("address_drift_miles", 0.0),
        red_flags = [],
        requires_human_review = False,

        # Structured fraud object (prevents LangSmith crashes)
        fraud = FraudSignals(
            refund_count = session_metadata.get("refund_count", 0),
            address_drift_miles = session_metadata.get("address_drift_miles", 0.0),
            red_flags = [],
            requires_human_review = False,
            summary = "",
        ),
    )

    # Compile and invoke the agent graph
    graph = build_agent_graph().compile()
    final_state = graph.invoke(initial_state)

    return final_state

# Demo with LangSmith Integration
if __name__ == "__main__":
    demo_input = "Show my last order"
    demo_session = {
        "user_id": os.getenv("USER_ID"),
        "email": os.getenv("USER_EMAIL"),
        "ip_address": "73.15.182.91",
        "geo_location": "TX",
        "device_id": "demo-device",
        "refund_count": 0,
        "address_drift_miles": 0.0
    }

    # Initialize LangSmith client and start a trace
    client = Client()
    trace_id = client.start_trace(name = "Demo Agent Run")

    # Run the agent
    final_state = run_agent(demo_input, demo_session)
    final_state.trace_id = trace_id

    # Log full agent state to LangSmith
    client.log_state(trace_id, final_state.dict())

    # End the LangSmith trace
    client.end_trace(trace_id)

    # Print final state
    print("Final AgentState:")
    print(final_state.dict())
