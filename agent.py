# agent.py
import os
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from nodes.verify_identity import verify_identity_node
from nodes.red_flag_checker import red_flag_checker_node
from nodes.risk_scoring import risk_scoring_node
from nodes.human_review import human_review_node
from nodes.draft_response import draft_response_node

load_dotenv()


def route_next_step(state: AgentState) -> str:
    status = state.status
    status_value = status.value if hasattr(status, "value") else status

    if status_value == "IDENTITY_FAILED" or not state.is_verified:
        return "blocked"

    if status_value == "HUMAN_REVIEW_REQUIRED" or state.requires_human_review:
        return "human_review"

    if status_value == "DRAFT_READY":
        return "draft"

    if status_value in {"HUMAN_APPROVED"}:
        return "approved"

    if status_value in {"HUMAN_REJECTED"}:
        return "rejected"

    if status_value in {"DATA_RETRIEVED", "FLAGS_CHECKED", "RISK_SCORED"}:
        return "continue"

    return "continue"


def build_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("verify_identity", verify_identity_node)
    graph.add_node("red_flag_check", red_flag_checker_node)
    graph.add_node("risk_scoring", risk_scoring_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("draft_response", draft_response_node)

    graph.add_edge(START, "verify_identity")

    graph.add_conditional_edges(
        "verify_identity",
        route_next_step,
        {
            "blocked": END,
            "continue": "red_flag_check",
            "human_review": "human_review",
            "draft": "draft_response",
        },
    )

    graph.add_conditional_edges(
        "red_flag_check",
        route_next_step,
        {
            "human_review": "human_review",
            "auto_approve": "risk_scoring",
            "continue": "risk_scoring",
            "draft": "draft_response",
        },
    )

    graph.add_conditional_edges(
        "risk_scoring",
        route_next_step,
        {
            "human_review": "human_review",
            "draft": "draft_response",
            "continue": "draft_response",
        },
    )

    graph.add_conditional_edges(
        "human_review",
        route_next_step,
        {
            "approved": "draft_response",
            "rejected": END,
            "continue": "draft_response",
        },
    )

    graph.add_edge("draft_response", END)

    return graph


def run_agent(user_input: str, session_metadata: dict) -> dict:
    graph = build_agent_graph().compile()
    graph.name = "ecomm_agent_graph"

    initial_state = AgentState(
        user_input=user_input,
        session_metadata=session_metadata,
        is_verified=False,
        contains_pii=False,
        refund_count=session_metadata.get("refund_count", 0),
        address_drift_miles=session_metadata.get("address_drift_miles", 0.0),
        red_flags=[],
        requires_human_review=False,
        human_decision=None,
    )

    final_state = graph.invoke(
        initial_state,
        config={
            "run_name": "ecomm_agent_run",
            "tags": ["local-demo"],
            "metadata": {
                "user_id": session_metadata.get("user_id"),
            },
        },
    )

    if isinstance(final_state, AgentState):
        return final_state.model_dump()

    return final_state


if __name__ == "__main__":
    demo_input = "Show my last order"
    demo_session = {
        "user_id": os.getenv("TRUSTED_USER_ID", "demo_user_123"),
        "email": os.getenv("TRUSTED_USER_EMAIL", "user@example.com"),
        "ip_address": "73.15.182.91",
        "geo_location": "TX",
        "device_id": "demo-device",
        "refund_count": 0,
        "address_drift_miles": 0,
    }

    output = run_agent(demo_input, demo_session)
    print("Final agent state:")
    print(output)

    status = output.get("status")
    status_value = status.value if hasattr(status, "value") else status

    assert status_value in {
        "IDENTITY_REQUIRED",
        "IDENTITY_VERIFIED",
        "IDENTITY_FAILED",
        "DATA_RETRIEVED",
        "FLAGS_CHECKED",
        "RISK_SCORED",
        "HUMAN_REVIEW_REQUIRED",
        "HUMAN_APPROVED",
        "HUMAN_REJECTED",
        "DRAFT_READY",
        "DONE",
        None,
    }