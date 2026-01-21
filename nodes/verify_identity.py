"""
verify_identity.py

Identity verification (HITL security gate) node.

Purpose:
- Prevent access to PII or financial actions without verification
- Enforce a mandatory identity challenge for sensitive requests
- Halt the agent safely until verification is completed

Design rules:
- No external calls
- No database access
- Uses .env for demo identity matching
- Updates state only (no side effects)
"""

import os
from agent.state import AgentState

def verify_identity_node(state: AgentState) -> AgentState:
    """
    Verifies the user's identity before allowing access to sensitive data.

    In production, this could involve:
    - OTP verification
    - OAuth / SSO
    - Knowledge-based authentication

    In this demo:
    - Identity is validated against trusted values in .env
    """

    # Determine whether this request is sensitive
    sensitive_keywords = ["refund", "order", "account", "address", "show my last order"] # For the demo triggers identity check, so I included "show my last order" in keywords

    is_sensitive = any(
        keyword in state.user_input.lower()
        for keyword in sensitive_keywords
    )

    # Non-sensitive requests may proceed without identity checks
    if not is_sensitive:
        state.is_verified = True
        state.status = "NON_SENSITIVE_REQUEST"
        return state

    # Load trusted identity from .env
    trusted_user_id = os.getenv("TRUSTED_USER_ID")
    trusted_user_email = os.getenv("TRUSTED_USER_EMAIL")

    # Identity information provided by the session
    provided_user_id = state.session_metadata.get("user_id")
    provided_email = state.session_metadata.get("email")

    # No identity provided -> pause for HITL challenge
    if not provided_user_id or not provided_email:
        state.is_verified = False
        state.status = "IDENTITY_REQUIRED"
        return state

    # Identity validation check
    if (
        provided_user_id == trusted_user_id
        and provided_email == trusted_user_email
    ):
        state.is_verified = True
        state.status = "IDENTITY_VERIFIED"
        return state

    # Identity failed -> hard stop
    state.is_verified = False
    state.status = "IDENTITY_FAILED"

    return state
