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

    # Load policy thresholds from .env
    max_refunds = int(os.environ["MAX_REFUNDS_PER_MONTH"])
    max_drift_miles = float(os.environ["ADDRESS_DRIFT_THRESHOLD_MILES"])

    # Extract signals from state
    refund_count = state.refund_count
    address_drift_miles = state.address_drift_miles

    # Refund velocity check
    if refund_count > max_refunds:
        state.red_flags.append(RiskFlag.REFUND_VELOCITY)
        state.requires_human_review = True

    # Address drift check
    if address_drift_miles > max_drift_miles:
        state.red_flags.append(RiskFlag.GEO_MISMATCH)
        state.requires_human_review = True

    # Update status
    if state.red_flags:
        state.status = AgentStatus.FLAGS_CHECKED
    else:
        state.status = AgentStatus.FLAGS_CHECKED

    return state
