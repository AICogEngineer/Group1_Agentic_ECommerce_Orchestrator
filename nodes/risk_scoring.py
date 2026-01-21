"""
risk_scoring.py

Behavioral risk scoring node.

Purpose:
- Compute a composite trust score for the user based on historical and current signals
- Flag users for human review if the trust score is below a threshold
- Update AgentState fields for routing to human review or automated actions
"""

from agent.state import AgentState, AgentStatus, RiskFlag

# Default threshold below which human review is required
TRUST_SCORE_THRESHOLD = 0.5

def risk_scoring_node(state: AgentState) -> AgentState:
    """
    Computes trust score and determines whether a human review is required.

    Updates the AgentState:
    - state.fraud.trust_score
    - state.requires_human_review
    - state.status
    """

    # Extract current fraud signals
    refund_count = state.fraud.refund_count if state.fraud else 0
    address_drift = state.fraud.address_drift_miles if state.fraud else 0.0

    # Compute a simple trust score
    # Higher refund count and higher address drift reduce trust
    # Score normalized between 0 and 1
    trust_score = 1.0 # Start fully trusted

    # Penalize excessive refunds
    if refund_count > 0:
        trust_score -= min(0.3, 0.05 * refund_count) # Each refund reduces score up to 0.3 max

    # Penalize significant address drift
    if address_drift > 0:
        trust_score -= min(0.3, address_drift / 1000.0) # Each 1000 miles reduces score up to 0.3 max

    # Clamp trust_score between 0 and 1
    trust_score = max(0.0, min(1.0, trust_score))

    # Update fraud object
    if state.fraud:
        state.fraud.trust_score = trust_score
    else:
        from agent.state import FraudSignals
        state.fraud = FraudSignals(
            refund_count = refund_count,
            address_drift_miles = address_drift,
            red_flags = [],
            requires_human_review = False,
            summary="Auto-generated fraud summary for trust scoring"
        )
        state.fraud.trust_score = trust_score

    # Determine if human review is required
    if trust_score < TRUST_SCORE_THRESHOLD or (state.fraud.red_flags if state.fraud else []):
        state.requires_human_review = True
        state.status = AgentStatus.HUMAN_REVIEW_REQUIRED
    else:
        state.requires_human_review = False
        state.status = AgentStatus.RISK_SCORED

    # Optionally log reason for audit
    reason_summary = (
        f"Refunds: {refund_count}, "
        f"Address drift: {address_drift} miles, "
        f"Trust score: {trust_score:.2f}"
    )
    if state.fraud:
        state.fraud.summary = reason_summary

    return state