"""
human_review.py

Human-in-the-Loop (HITL) approval node.

Purpose:
- Pause execution for high-risk or flagged requests
- Present context and agent reasoning to a human reviewer
- Resume or terminate execution based on human decision

This node represents mandatory human oversight.
"""

from agent.state import AgentState

def human_review_node(state: AgentState) -> AgentState:
    """
    Simulates a human approval step.

    In production, this would:
    - Display flags, reasoning, and draft responses in a UI
    - Allow a human to approve, edit, or reject the action

    In this demo:
    - Approval is mocked via state.human_decision
    """

    # Ensure this node is only reached intentionally
    state.status = "AWAITING_HUMAN_REVIEW"

    # Mocked human decision (for demo purposes)
        # Expected values: "approved", "rejected", or None
    decision = getattr(state, "human_decision", None)

    if decision == "approved":
        state.status = "HUMAN_APPROVED"
        state.requires_human_review = False
        return state

    if decision == "rejected":
        state.status = "HUMAN_REJECTED"
        return state

    # No decision yet -> execution pauses here
    return state
