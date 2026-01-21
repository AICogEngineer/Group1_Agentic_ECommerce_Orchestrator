"""
draft_response.py

Drafting responses node.

Purpose:
- Create chat/email response based on agent reasoning and retrieved data
- Populates AgentState.draft
"""

from agent.state import AgentState, AgentStatus

def draft_response_node(state: AgentState) -> AgentState:
    """
    Prepares draft response from retrieved data and agent reasoning.

    This node assumes:
    - Identity has been verified
    - Risk checks have passed or been approved by a human
    """

    order_info = state.retrieved.order_data if state.retrieved else {}
    state.draft = {
        "channel": "chat",
        "subject": None,
        "body": f"Here is the information for your order: {order_info}",
        "internal_notes": "Auto-generated draft response"
    }

    # Final status update
    state.status = AgentStatus.DRAFT_READY

    return state
