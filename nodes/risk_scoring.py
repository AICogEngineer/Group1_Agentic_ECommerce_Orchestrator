"""
risk_scoring.py

Behavioral risk scoring node.

Purpose:
- Aggregate detected red flags into a single trust / risk signal
- Decide whether the agent may proceed autonomously
- Escalate borderline or low-trust cases to Human-in-the-Loop (HITL)

Design rules:
- No external calls
- No side effects
- Only reads and updates AgentState
"""

from agent.state import AgentState

def risk_scoring_node(state: AgentState) -> AgentState:
    """
    Calculates a simple trust score based on accumulated red flags.

    In production, this could be:
    - A weighted rules engine
    - A statistical model
    - A learned risk classifier

    For this demo:
    - 0 flags  -> High trust
    - 1 flag   -> Medium trust (low priority human review)
    - 2+ flags -> Low trust (top priority human review)
    """

    red_flag_count = len(state.red_flags)

    # High trust: safe to continue autonomously
    if red_flag_count == 0:
        state.trust_score = "HIGH"
        state.status = "RISK_ACCEPTABLE"
        state.requires_human_review = False
        return state

    # Medium trust: human review recommended
    if red_flag_count == 1:
        state.trust_score = "MEDIUM"
        state.status = "RISK_REVIEW_RECOMMENDED"
        state.requires_human_review = True
        return state

    # Low trust: human review mandatory
    state.trust_score = "LOW"
    state.status = "RISK_TOO_HIGH"
    state.requires_human_review = True

    return state
