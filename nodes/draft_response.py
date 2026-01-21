"""
draft_response.py

Drafting responses node.

Purpose:
- Prepare a safe, human-reviewable response
- Explain the reasoning behind the decision
- NEVER send or execute actions directly

Design rules:
- No I/O
- No messaging APIs
- No irreversible actions
"""

from agent.state import AgentState

def draft_response_node(state: AgentState) -> AgentState:
    """
    Drafts a user-facing response based on the agent's reasoning.

    This node assumes:
    - Identity has been verified
    - Risk checks have passed or been approved by a human
    """

    # Build explanation for transparency
    reasoning_summary = []

    if state.trust_score:
        reasoning_summary.append(f"Trust level assessed as {state.trust_score}")

    if state.red_flags:
        reasoning_summary.append(f"Red flags reviewed: {', '.join(state.red_flags)}")
    else:
        reasoning_summary.append("No fraud or policy violations detected")

    # Draft a safe, reviewable response
    state.draft_response = {
        "subject": "Regarding Your Recent Request",
        "body": (
            "Hi,\n\n"
            "We’ve reviewed your request using our security verification and policy checks.\n\n"
            f"Summary:\n- " + "\n- ".join(reasoning_summary) + "\n\n"
            "If applicable, a support agent will finalize the next steps.\n\n"
            "Thank you for using us for your drafting needs."
        )
    }

    # Final status update
    state.status = "RESPONSE_DRAFTED"

    return state
