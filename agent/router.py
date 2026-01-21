"""
router.py

Centralized routing logic for the Agentic E-Commerce Orchestrator.

Purpose:
- Decide the next graph transition based on agent state
- Enforce security, fraud, and HITL gating rules
- Keep routing logic separate from node execution

Design principles:
- Pure function: no side effects
- Deterministic and auditable
- Easy to reason about during safety reviews
"""

from agent.state import AgentState


def route_next_step(state: AgentState) -> str:
    """
    Determines the next step in the LangGraph workflow.

    This function is used by LangGraph's `add_conditional_edges`
    and must return a string key that matches a defined edge.

    Routing priorities (highest → lowest):
    1. Identity enforcement (hard security gate)
    2. Human-in-the-loop escalation
    3. Normal autonomous continuation
    """

    # 1. Identity verification gate
    if not state.is_verified:
        return "blocked"

    # 2. Human-in-the-loop required (risk or fraud)
    if state.requires_human_review:
        return "human_review"

    # 3. Post–human review decisions
    if state.status == "HUMAN_APPROVED":
        return "approved"

    if state.status == "HUMAN_REJECTED":
        return "rejected"

    # 4. Normal autonomous continuation
    return "continue" # Used after successful verification, low risk and no policy violations
