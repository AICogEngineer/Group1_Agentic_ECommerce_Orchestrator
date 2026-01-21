"""
red_flag_checker.py

Fraud and risk detection node.

Purpose:
- Evaluate predefined red-flag rules before high-stakes actions
- Prevent unsafe autonomous execution
- Route risky cases into Human-in-the-Loop review

This node NEVER performs side effects.
It only evaluates risk and updates agent state.
"""

import os
from agent.state import AgentState

def red_flag_checker_node(state: AgentState) -> AgentState:
    """
    Checks for fraud and risk signals derived from policy rules and historical user behavior.

    Red flags implemented:
    - Refund velocity (too many refunds in a short period)
    - Address / location drift
    """

    # Load policy thresholds from .env 
    max_refunds = int(os.getenv("MAX_REFUNDS_PER_MONTH", 3))
    max_drift_miles = int(os.getenv("ADDRESS_DRIFT_THRESHOLD_MILES", 300))

    # Extract signals from state (populated earlier) 
    refund_count = state.refund_count or 0
    address_drift_miles = state.address_drift_miles or 0

    # Refund velocity check 
    if refund_count > max_refunds:
        state.red_flags.append("REFUND_VELOCITY_EXCEEDED")
        state.requires_human_review = True

    # Address / geo drift check 
    if address_drift_miles > max_drift_miles:
        state.red_flags.append("ADDRESS_DISTANCE_DISCREPANCY")
        state.requires_human_review = True

    # Update status for routing 
    if state.red_flags:
        state.status = "RED_FLAG_DETECTED"
    else:
        state.status = "NO_RED_FLAGS"

    return state
