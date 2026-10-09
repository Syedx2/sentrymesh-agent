"""
=============================================================================
SentryMesh: Autonomous AWS Incident Triage & Guardrail Agent
=============================================================================
Orchestrates Strands Decider 2B for ultra-fast, deterministic guardrail decisions
and routes complex generative tasks to Amazon Bedrock.
Enforces non-bypassable hard-floor safety checks.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from agent.decider_engine import StrandsDeciderEngine
from agent.bedrock_client import BedrockAgentClient
from agent.aws_tools import AWSToolRegistry
from decider_patterns.cloud_guardrail_pattern import (
    GuardrailEvaluationRequest,
    GuardrailAction,
)


class IncidentPayload(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"inc-{uuid.uuid4().hex[:6]}")
    title: str
    service: str
    severity: str = "P2-High"
    environment: str = "production"
    proposed_remediation_tool: str
    tool_arguments: Dict[str, Any] = Field(default_factory=dict)
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class IncidentTriageResult(BaseModel):
    incident_id: str
    status: str
    decider_action: str
    decider_confidence: float
    decider_confidence_pct: str
    decider_candidate_scores: Dict[str, float]
    decider_latency_ms: float
    is_live_model: bool = False
    is_live_bedrock: bool = False
    remediation_result: Dict[str, Any] = Field(default_factory=dict)
    bedrock_synthesis: Dict[str, Any] = Field(default_factory=dict)
    total_pipeline_latency_ms: float
    estimated_cost_usd: float
    cost_savings_vs_pure_llm_pct: float


class SentryMeshAgent:
    """
    Main Autonomous Agent Engine.
    """

    def __init__(self, region: str = "us-east-1", decider_endpoint: Optional[str] = None):
        self.decider = StrandsDeciderEngine(endpoint_url=decider_endpoint)
        self.bedrock = BedrockAgentClient(region_name=region)
        self.history: Dict[str, IncidentTriageResult] = {}
        self.pending_approvals: Dict[str, IncidentPayload] = {}

    def triage_incident(self, incident: IncidentPayload) -> IncidentTriageResult:
        """
        Executes the autonomous triage pipeline:
        1. Strands Decider 2B evaluates guardrail & blast radius (~115ms).
        2. If PROCEED: Evaluates via AWSToolRegistry without bypass.
           If tool requires human confirmation, hard-floor safety escalates to ESCALATED_FOR_APPROVAL.
        3. If CONFIRM: Pauses and queues for human DevOps sign-off.
        4. If DENY: Blocks execution.
        5. Amazon Bedrock generates post-incident RCA & executive summary.
        """
        pipeline_start = time.perf_counter()

        blast_radius = "high" if incident.severity in ["P1-Critical", "P0"] else "medium"
        if "flush" in incident.proposed_remediation_tool or "read" in incident.proposed_remediation_tool:
            blast_radius = "low"

        guardrail_req = GuardrailEvaluationRequest(
            incident_type=incident.title,
            proposed_tool=incident.proposed_remediation_tool,
            tool_arguments=incident.tool_arguments,
            environment=incident.environment,
            blast_radius=blast_radius,
            user_context=f"Service: {incident.service} | Severity: {incident.severity}",
        )

        decision = self.decider.evaluate_guardrail(guardrail_req)

        # Step 2: Tool Execution with Hard-Floor Enforcement (No model bypass)
        remediation_res = {}
        if decision.action == GuardrailAction.PROCEED:
            # execute_tool called WITHOUT confirmed=True; hard floor enforces confirmation if tool catalog requires it
            remediation_res = AWSToolRegistry.execute_tool(
                incident.proposed_remediation_tool,
                incident.tool_arguments,
                confirmed=False,
            )
            if remediation_res.get("requires_human_approval"):
                status = "ESCALATED_FOR_APPROVAL"
                self.pending_approvals[incident.incident_id] = incident
            elif remediation_res.get("status") == "SUCCESSFULLY_APPLIED":
                status = "RESOLVED_AUTONOMOUSLY"
            else:
                status = "BLOCKED_BY_SAFETY_FLOOR"
        elif decision.action == GuardrailAction.CONFIRM:
            remediation_res = {
                "status": "AWAITING_HUMAN_APPROVAL",
                "message": "High blast radius detected. Action dispatched to DevOps on-call channel.",
            }
            status = "ESCALATED_FOR_APPROVAL"
            self.pending_approvals[incident.incident_id] = incident
        else:
            remediation_res = {
                "status": "BLOCKED_BY_GUARDRAIL",
                "message": decision.reasoning,
            }
            status = "ACTION_DENIED"

        # Step 3: Amazon Bedrock Generative Root Cause Analysis
        bedrock_res = self.bedrock.generate_incident_synthesis(
            incident_title=incident.title,
            telemetry=incident.telemetry,
            guardrail_action=decision.action.value,
        )

        total_latency = round((time.perf_counter() - pipeline_start) * 1000 + decision.decision_latency_ms, 2)
        pure_llm_cost = 0.0150
        actual_cost = 0.0001 + (bedrock_res.get("estimated_cost_usd", 0.0035))
        savings_pct = round(((pure_llm_cost - actual_cost) / pure_llm_cost) * 100, 1)

        result = IncidentTriageResult(
            incident_id=incident.incident_id,
            status=status,
            decider_action=decision.action.value,
            decider_confidence=decision.confidence,
            decider_confidence_pct=f"{decision.confidence * 100:.1f}%",
            decider_candidate_scores=decision.candidate_scores,
            decider_latency_ms=decision.decision_latency_ms,
            is_live_model=decision.is_live_model,
            is_live_bedrock=bedrock_res.get("is_live_bedrock", False),
            remediation_result=remediation_res,
            bedrock_synthesis=bedrock_res,
            total_pipeline_latency_ms=total_latency,
            estimated_cost_usd=round(actual_cost, 5),
            cost_savings_vs_pure_llm_pct=savings_pct,
        )

        self.history[incident.incident_id] = result
        return result

    def approve_incident(self, incident_id: str, operator_id: str = "devops-oncall") -> Dict[str, Any]:
        """
        Human-in-the-Loop approval method.
        Explicitly provides `confirmed=True` to execute a queued high-blast radius tool.
        """
        if incident_id not in self.pending_approvals:
            return {"success": False, "error": f"No pending approval found for incident {incident_id}"}

        incident = self.pending_approvals.pop(incident_id)
        exec_res = AWSToolRegistry.execute_tool(
            incident.proposed_remediation_tool,
            incident.tool_arguments,
            confirmed=True,  # Human explicitly authorized
        )

        if incident_id in self.history:
            self.history[incident_id].status = "RESOLVED_WITH_HUMAN_APPROVAL"
            self.history[incident_id].remediation_result = exec_res

        return {
            "success": True,
            "incident_id": incident_id,
            "operator_id": operator_id,
            "execution_result": exec_res,
        }
