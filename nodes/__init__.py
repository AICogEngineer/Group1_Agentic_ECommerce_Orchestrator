"""
nodes package

Purpose:
- Contains all executable graph nodes for the agent workflow
- Each file represents ONE atomic, auditable step

Design rules:
- Nodes are pure functions: (state) -> state
- No direct graph control
- No direct user-facing output
- No autonomous side effects

Security principle:
- High-risk actions are gated and escalated, never executed directly
"""
