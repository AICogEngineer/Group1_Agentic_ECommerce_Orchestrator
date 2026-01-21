"""
state.py

Central AgentState definitions for the Agentic E-Commerce Orchestrator.

Purpose:
- Represent all information flowing through the agent graph
- Include PII, session metadata, fraud signals, HITL data, and draft responses
- Fully auditable and validation-ready
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, ValidationError, confloat, conint

# Enumerations
class AgentStatus(str, Enum):
    """Defines all possible lifecycle stages of the agent."""
    IDENTITY_REQUIRED = "IDENTITY_REQUIRED"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    IDENTITY_FAILED = "IDENTITY_FAILED"

    DATA_RETRIEVED = "DATA_RETRIEVED"
    FLAGS_CHECKED = "FLAGS_CHECKED"
    RISK_SCORED = "RISK_SCORED"

    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"

    DRAFT_READY = "DRAFT_READY"
    DONE = "DONE"

class Intent(str, Enum):
    """User intent types, used to drive downstream reasoning and routing."""
    REFUND = "refund"
    RETURN = "return"
    SHIPPING_ISSUE = "shipping_issue"
    BILLING_DISPUTE = "billing_dispute"
    ACCOUNT_TAKEOVER = "account_takeover"
    OTHER = "other"

class RiskFlag(str, Enum):
    """Fraud and risk indicators that may trigger HITL gating."""
    REFUND_VELOCITY = "refund_velocity"
    RETURNLESS_VELOCITY = "returnless_velocity"
    GEO_MISMATCH = "geo_mismatch"
    CHARGEBACK_HISTORY = "chargeback_history"
    SERIAL_REFUNDER = "serial_refunder"
    LEGAL_THREAT = "legal_threat"
    ATO_SUSPECTED = "ato_suspected"
    POLICY_OUT_OF_WINDOW = "policy_out_of_window"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

class HumanDecisionType(str, Enum):
    """Possible human reviewer actions."""
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    NEEDS_MORE_INFO = "needs_more_info"

# Pydantic Models
class IntentExtraction(BaseModel):
    """Captures the extracted intent from user input."""
    intent: Intent = Field(description = "Primary user intent")

    user_id: Optional[str] = Field(None, description = "User identifier if present in the request")
    order_id: Optional[str] = Field(None, description = "Order identifier if present in the request")

    # Confidence in intent extraction (0 <= confidence <= 1)
    confidence: float = Field(..., ge = 0, le = 1, description = "Model confidence in the extracted intent")

    rationale: str = Field(description = "Brief explanation of how intent was derived")

class FraudSignals(BaseModel):
    """Stores all fraud and risk-related signals."""
    # Number of refunds in the recent window (cannot be negative)
    refund_count: int = Field(0, ge = 0, description = "Number of refunds in the recent window")
    # Distance between shipping address and session location (cannot be negative)
    address_drift_miles: float = Field(0.0, ge = 0, description = "Distance between shipping address and session location")

    red_flags: List[RiskFlag] = Field(description = "Triggered fraud or abuse indicators")
    trust_score: Optional[float] = Field(None, ge = 0, le = 1, description = "Composite trust score (0 = low, 1 = high)") # Composite trust score (0 = low, 1 = high)
    requires_human_review: bool = Field(description = "Whether execution must be gated by a human")

    summary: str = Field(description = "One-paragraph explanation for reviewers and audit logs")

class RetrievalOutputs(BaseModel):
    """Holds outputs from multi-source reasoning (Snowflake & Pinecone)."""
    order_data: Dict[str, Any] = Field(description = "Structured order and customer data")
    policy_context: Dict[str, Any] = Field(description = "Policy clauses relevant to the request")

class DraftResponse(BaseModel):
    """Prepared response for human review or user communication."""
    channel: Literal["chat", "email"] = Field(description = "Delivery channel for the draft")
    subject: Optional[str] = Field(None, description = "Email subject if applicable")
    body: str = Field(description="Customer-visible response text")

    internal_notes: Optional[str] = Field(None, description = "Internal reviewer notes (not sent)")

class HumanDecision(BaseModel):
    """Represents a human reviewer decision for HITL nodes."""
    type: HumanDecisionType = Field(description = "Type of decision")
    reason: Optional[str] = Field(None, description = "Reason for the decision")
    edits: Optional[Dict[str, Any]] = Field(None, description = "Edits applied when type == EDIT")

class HITLResumePayload(BaseModel):
    """Collection of human decisions to resume execution."""
    decisions: List[HumanDecision] = Field(description = "Decisions applied by the human reviewer")

# Agent State
class AgentState(BaseModel):
    """
    The central agent state object.
    Contains user input, session info, verification, fraud signals,
    HITL data, reasoning outputs, and draft response.
    """

    # Allow extra fields for flexibility
    model_config = ConfigDict(extra = "allow")

    # User / Session
    user_input: str = Field(description = "Raw user message")
    session_metadata: Dict[str, Any] = Field(
        default_factory = dict, description = "Session context: IP, geo, device, or session context"
    )

    intent: Intent = Field(Intent.OTHER, description = "Parsed user intent")
    user_id: Optional[str] = None
    order_id: Optional[str] = None

    is_verified: bool = Field(False, description = "Identity verification result")
    contains_pii: bool = Field(False, description = "Whether input contained PII")

    status: Optional[AgentStatus] = Field(None, description = "Current lifecycle stage")

    # Fraud / Risk
    refund_count: int = Field(0, ge = 0, description = "Number of refunds in the recent window")
    address_drift_miles: float = Field(0.0, ge = 0, description = "Distance between shipping address and session location")

    red_flags: List[RiskFlag] = Field(default_factory = list)
    requires_human_review: bool = False

    fraud: Optional[FraudSignals] = Field(default_factory = FraudSignals)
    retrieved: Optional[RetrievalOutputs] = None

    # HITL / Human Review
    hitl_resume: Optional[HITLResumePayload] = None
    human_notes: Optional[str] = None

    # Draft / Response
    draft: Optional[DraftResponse] = None

    # Logging / Tracing
    trace_id: Optional[str] = Field(None, description = "Trace identifier for LangSmith / logging")

    # Override dict to allow flexible dumping
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return self.model_dump(*args, **kwargs)

# Helper Function
def safe_validate_state(data: Dict[str, Any]) -> AgentState:
    """
    Validates a dictionary as a proper AgentState.
    Raises RuntimeError if validation fails.
    """
    try:
        return AgentState.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"Invalid AgentState: {e}") from e
    