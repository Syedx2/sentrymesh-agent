"""
=============================================================================
Reusable Strands Decider 2B Decision Pattern: AWS Cloud Guardrail & Action Triage
Pattern Tag: #guardrails / #tool-selection
=============================================================================

What it does:
------------
This decision pattern intercepts autonomous AWS cloud actions (e.g. EC2 reboots,
IAM quarantine, cache flushes, resource termination) before execution.
It uses Strands Decider 2B to evaluate the action's safety, intent alignment,
and risk level in ~115ms with calibrated confidence scores.

Decision Outputs:
- PROCEED: Action is verified, grounded, and safe for automated execution.
- GUIDE: Action parameters need slight adjustment/re-scoping.
- CONFIRM: High-blast-radius action requires human DevOps confirmation.
- DENY: Unauthorized, hallucinated, or destructive violation blocked.
"""

from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class GuardrailAction(str, Enum):
    PROCEED = "Proceed"
    GUIDE = "Guide"
    CONFIRM = "Confirm"
    DENY = "Deny"


class GuardrailEvaluationRequest(BaseModel):
    incident_type: str = Field(..., description="Type of incident or cloud alarm (e.g., 'HighMemoryPressure', 'UnusualRootAPI')")
    proposed_tool: str = Field(..., description="Name of the AWS tool/action the agent wants to invoke")
    tool_arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the proposed tool")
    environment: str = Field(default="production", description="Environment: production, staging, development")
    blast_radius: str = Field(default="medium", description="Estimated blast radius: low, medium, high, critical")
    user_context: str = Field(default="", description="Original user prompt or automated CloudWatch event payload")


class GuardrailDecision(BaseModel):
    action: GuardrailAction
    confidence: float
    reasoning: str
    decision_latency_ms: float
    candidate_scores: Dict[str, float]


# ---------------------------------------------------------------------------
# Reusable Strands Decider 2B Pattern Definition
# ---------------------------------------------------------------------------
class CloudGuardrailDecisionPattern:
    """
    Reusable decision pattern that wires Strands Decider 2B into an agent's execution path.
    """

    QUESTION_TEMPLATE = (
        "Given the incident context, proposed tool '{tool}', arguments {args}, "
        "target environment '{env}', and estimated blast radius '{blast}', "
        "should this autonomous cloud action Proceed, Guide with safer params, "
        "require human Confirm, or Deny immediately?"
    )

    OPTIONS = [
        GuardrailAction.PROCEED.value,
        GuardrailAction.GUIDE.value,
        GuardrailAction.CONFIRM.value,
        GuardrailAction.DENY.value,
    ]

    @classmethod
    def build_prompt(cls, request: GuardrailEvaluationRequest) -> Tuple[str, List[str]]:
        """
        Formats the typed question and options for the Strands Decider 2B model.
        """
        question = cls.QUESTION_TEMPLATE.format(
            tool=request.proposed_tool,
            args=request.tool_arguments,
            env=request.environment,
            blast=request.blast_radius,
        )
        return question, cls.OPTIONS
