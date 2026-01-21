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

# Define keywords mapping to intents
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
    
    In production, this would check PII, auth tokens, or external identity providers.    
    """

    # Load trusted credentials from environment
    trusted_user_id = os.environ["TRUSTED_USER_ID"]
    trusted_user_email = os.environ["TRUSTED_USER_EMAIL"]

    # Extract session metadata
    session_user_id = state.session_metadata.get("user_id")
    session_email = state.session_metadata.get("email")

    # Identity verification
    if session_user_id == trusted_user_id and session_email == trusted_user_email:
        state.is_verified = True
        state.status = AgentStatus.IDENTITY_VERIFIED
    else:
        state.is_verified = False
        state.status = AgentStatus.IDENTITY_REQUIRED

    # Set intent based on user input keywords
    user_input_lower = state.user_input.lower()
    detected_intent = Intent.OTHER # Default
    for keyword, intent_enum in INTENT_KEYWORDS.items():
        if keyword in user_input_lower:
            detected_intent = intent_enum
            break

    state.intent = detected_intent

    # Marks PII if user_id/email present
    if "@" in state.user_input or any(c.isdigit() for c in state.user_input):
        state.contains_pii = True

    return state
