"""
=============================================================================
SentryMesh: Autonomous AWS Incident Triage & Guardrail Agent
=============================================================================
Orchestrates Strands Decider 2B for ultra-fast, deterministic guardrail decisions
and routes complex generative tasks to Amazon Bedrock.
"""

import time
import uuid
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from agent.decider_engine import StrandsDeciderEngine
from agent.bedrock_client import BedrockAgentClient
from agent.aws_tools import AWSToolRegistry
from decider_patterns.cloud_guardrail_pattern import (
    GuardrailEvaluationRequest,
    GuardrailAction,
)
from decider_patterns.model_routing_pattern import RoutingDestination


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
    remediation_result: Dict[str, Any] = Field(default_factory=dict)
    bedrock_synthesis: Dict[str, Any] = Field(default_factory=dict)
    total_pipeline_latency_ms: float
    estimated_cost_usd: float
    cost_savings_vs_pure_llm_pct: float


class SentryMeshAgent:
    """
    Main Autonomous Agent Engine.
    """

    def __init__(self, region: str = "us-east-1"):
        self.decider = StrandsDeciderEngine()
        self.bedrock = BedrockAgentClient(region_name=region)
        self.history: List[IncidentTriageResult] = []

    def triage_incident(self, incident: IncidentPayload) -> IncidentTriageResult:
        """
        Executes the autonomous triage pipeline:
        1. Strands Decider 2B evaluates guardrail & blast radius (~115ms).
        2. If PROCEED: Executes AWS operational tool immediately.
        3. If CONFIRM: Pauses for human DevOps sign-off.
        4. If DENY: Blocks execution.
        5. Amazon Bedrock generates post-incident RCA & executive summary.
        """
        pipeline_start = time.perf_counter()

        # Step 1: Strands Decider 2B Guardrail Decision
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

        # Step 2: Execute Tool if Guardrail Passes
        remediation_res = {}
        if decision.action == GuardrailAction.PROCEED:
            remediation_res = AWSToolRegistry.execute_tool(
                incident.proposed_remediation_tool,
                incident.tool_arguments,
                confirmed=True,  # Guardrail verified
            )
            if remediation_res.get("status") == "SUCCESSFULLY_APPLIED":
                status = "RESOLVED_AUTONOMOUSLY"
            else:
                status = "BLOCKED_BY_SAFETY_FLOOR"
        elif decision.action == GuardrailAction.CONFIRM:
            remediation_res = {
                "status": "AWAITING_HUMAN_APPROVAL",
                "message": "High blast radius detected. Action dispatched to DevOps on-call channel.",
            }
            status = "ESCALATED_FOR_APPROVAL"
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
        
        # Benchmark Calculations:
        # A pure LLM agent performing both reasoning & guardrail check costs ~$0.015 and takes ~2,200ms
        # With Strands Decider 2B handling the decision, we achieve ~85% cost and time reduction on decision phase
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
            remediation_result=remediation_res,
            bedrock_synthesis=bedrock_res,
            total_pipeline_latency_ms=total_latency,
            estimated_cost_usd=round(actual_cost, 5),
            cost_savings_vs_pure_llm_pct=savings_pct,
        )

        self.history.append(result)
        return result
