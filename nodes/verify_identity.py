"""
verify_identity.py

Identity verification (HITL security gate) node.

Purpose:
- Ensure that user identity is validated before sensitive operations
- Gate the workflow for high-risk or PII-sensitive requests
- Update agent state with verification results
"""

import os
from agent.state import AgentState, AgentStatus, Intent

# Keyword-based intent hints (lightweight, deterministic)
INTENT_KEYWORDS = {
    "refund": Intent.REFUND,
    "return": Intent.RETURN,
    "shipping": Intent.SHIPPING_ISSUE,
    "billing": Intent.BILLING_DISPUTE,
    "account takeover": Intent.ACCOUNT_TAKEOVER
}

def verify_identity_node(state: AgentState) -> AgentState:
    """
    Verifies if the user's identity is trusted/verified before allowing access to sensitive data.
        - Identity is validated against trusted values in .env
        - .env is the single source of truth
    Determines intent based on keywords in user input.
    Relies exclusively on .env for trusted credentials. 
    """

    # Load trusted credentials from environment
    trusted_user_id = os.getenv("USER_ID")
    trusted_user_email = os.getenv("USER_EMAIL")

    # Fail closed if credentials are missing
    if not trusted_user_id or not trusted_user_email:
        state.is_verified = False
        state.status = AgentStatus.IDENTITY_FAILED
        return state
    
    # Extract session-provided identity
    session_user_id = state.session_metadata.get("user_id")
    session_email = state.session_metadata.get("email")

    # Verify identity
    if session_user_id == trusted_user_id and session_email == trusted_user_email:
        state.is_verified = True
        state.status = AgentStatus.IDENTITY_VERIFIED
    else:
        state.is_verified = False
        state.status = AgentStatus.IDENTITY_FAILED
        return state

    # Lightweight intent detection (routing hint only)
    user_input_lower = state.user_input.lower()
    state.intent = Intent.OTHER
    for keyword, intent in INTENT_KEYWORDS.items():
        if keyword in user_input_lower:
            state.intent = intent
            break

    # Mark potential PII exposure (conservative heuristic)
    state.contains_pii = bool(session_user_id or session_email)

    return state
