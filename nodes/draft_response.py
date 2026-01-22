"""
draft_response.py

Drafting responses node.

Purpose:
- Create chat/email response based on agent reasoning and retrieved data
- Populates AgentState.draft
"""

# nodes/draft_response.py
from agent.state import AgentState, DraftResponse, AgentStatus


def draft_response_node(state: AgentState) -> AgentState:
    order_data = {}
    if getattr(state, "retrieved", None) is not None and getattr(state.retrieved, "order_data", None) is not None:
        order_data = state.retrieved.order_data

    state.draft = DraftResponse(
        channel = "chat",
        subject = None,
        body = f"Here is the information for your order: {order_data}",
        internal_notes = "Auto-generated draft response",
    )
    state.status = AgentStatus.DRAFT_READY
    return state
