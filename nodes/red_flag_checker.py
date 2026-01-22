"""
red_flag_checker.py

Fraud and risk detection node.

Purpose:
- Evaluate predefined red-flag rules before high-stakes actions
- Prevent unsafe autonomous execution
- Route risky cases into Human-in-the-Loop review
"""

import os
from agent.state import AgentState, RiskFlag, AgentStatus

def red_flag_checker_node(state: AgentState) -> AgentState:
    """
    Checks refund velocity and address drift based on policy thresholds from .env.
    Updates AgentState with red flags and HITL requirement.
    """

    # Load thresholds from environment
    max_refunds = int(os.getenv("MAX_REFUNDS_PER_MONTH", "0"))
    max_drift_miles = float(os.getenv("ADDRESS_DRIFT_THRESHOLD_MILES", "0"))

    refund_count = state.refund_count
    address_drift = state.address_drift_miles

    red_flags: list[RiskFlag] = []

    # Refund velocity check
    if refund_count > max_refunds:
        red_flags.append(RiskFlag.REFUND_VELOCITY)

    # Geo mismatch check
    if address_drift > max_drift_miles:
        red_flags.append(RiskFlag.GEO_MISMATCH)

    # Update state-level flags
    state.red_flags = red_flags
    state.requires_human_review = bool(red_flags)

    # Keep FraudSignals authoritative and in sync
    if state.fraud:
        state.fraud.red_flags = red_flags
        state.fraud.requires_human_review = state.requires_human_review

    state.status = AgentStatus.FLAGS_CHECKED
    return state
