"""
human_review.py

Human-in-the-Loop (HITL) approval node.

Purpose:
- Pause execution for high-risk or flagged requests
- Present context, agent reasoning, and draft responses to a human reviewer
- Resume or terminate execution based on human decision
- Ensures safety before any high-stakes action is taken

This node represents mandatory human oversight.
"""

from agent.state import AgentState, AgentStatus, HumanDecisionType

def human_review_node(state: AgentState) -> AgentState:
    """
    Simulates a human approval step.

    Updates AgentState:
    - state.status: marks whether awaiting review, approved, or rejected
    - state.requires_human_review: gates further execution
    """

    # Ensure this node is only reached intentionally
    state.status = AgentStatus.HUMAN_REVIEW_REQUIRED
    state.requires_human_review = True

    # Get the human decision from the state
        # In production, this would come from a UI or API input
        # Expected values: "approve", "reject", "edit", "needs_more_info"
    decision = getattr(state, "human_decision", None)

    # Process the decision
    if decision == HumanDecisionType.APPROVE:
        state.status = AgentStatus.HUMAN_APPROVED
        state.requires_human_review = False
        return state

    if decision == HumanDecisionType.REJECT:
        state.status = AgentStatus.HUMAN_REJECTED
        return state # Keep requires_human_review True to indicate halt

    if decision == HumanDecisionType.EDIT: # In production, edits would be applied to the draft or notes, but here it is just marked as approved for demo purposes
        state.status = AgentStatus.HUMAN_APPROVED
        state.requires_human_review = False
        return state

    if decision == HumanDecisionType.NEEDS_MORE_INFO: # Pause execution until additional info is provided
        state.requires_human_review = True
        state.status = AgentStatus.HUMAN_REVIEW_REQUIRED
        return state

    # Execution pauses here if no decision
    return state
