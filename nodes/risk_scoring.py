"""
risk_scoring.py

Behavioral risk scoring node.

Purpose:
- Compute a composite trust score for the user based on historical and current signals
- Flag users for human review if the trust score is below a threshold
- Update AgentState fields for routing to human review or automated actions
"""

from agent.state import AgentState, AgentStatus

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

    # FraudSignals must exist at this point
    fraud = state.fraud
    if not fraud:
        state.requires_human_review = True
        state.status = AgentStatus.HUMAN_REVIEW_REQUIRED
        return state

    refund_count = fraud.refund_count
    address_drift = fraud.address_drift_miles

    # Higher refund count and higher address drift reduce trust
    # Score normalized between 0 and 1
    trust_score = 1.0 # Start fully trusted

    # Penalize refund behavior
    trust_score -= min(0.3, 0.05 * refund_count)

    # Penalize location inconsistency
    trust_score -= min(0.3, address_drift / 1000.0)

    # Clamp score
    trust_score = max(0.0, min(1.0, trust_score))

    fraud.trust_score = trust_score

    # Determine HITL requirement
    if trust_score < TRUST_SCORE_THRESHOLD or fraud.red_flags:
        state.requires_human_review = True
        fraud.requires_human_review = True
        state.status = AgentStatus.HUMAN_REVIEW_REQUIRED
    else:
        state.requires_human_review = False
        fraud.requires_human_review = False
        state.status = AgentStatus.RISK_SCORED

    # Human-readable audit summary
    fraud.summary = (
        f"Refunds={refund_count}, "
        f"Address drift={address_drift} miles, "
        f"Trust score={trust_score:.2f}"
    )

    return state
