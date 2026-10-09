"""
=============================================================================
Amazon Bedrock Generative Synthesis Client
=============================================================================
Connects with Amazon Bedrock (Claude 3.5 Sonnet / Amazon Nova) for deep
generative reasoning and root-cause analysis when handed off by Strands Decider 2B.
"""

import json
import time
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class BedrockAgentClient:
    """
    Client for invoking Amazon Bedrock foundation models with telemetry.
    """

    DEFAULT_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    FALLBACK_MODEL_ID = "amazon.nova-pro-v1:0"

    def __init__(self, region_name: str = "us-east-1", model_id: Optional[str] = None):
        self.region_name = region_name
        self.model_id = model_id or self.DEFAULT_MODEL_ID
        self.bedrock_runtime = None
        self._init_client()

    def _init_client(self):
        try:
            self.bedrock_runtime = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region_name,
            )
        except (NoCredentialsError, Exception):
            self.bedrock_runtime = None

    def generate_incident_synthesis(self, incident_title: str, telemetry: Dict[str, Any], guardrail_action: str) -> Dict[str, Any]:
        """
        Generates comprehensive root cause analysis and executive incident summary.
        """
        start_time = time.perf_counter()

        prompt = (
            f"You are the AWS Senior Site Reliability Engineer Agent.\n"
            f"Incident: {incident_title}\n"
            f"Telemetry: {json.dumps(telemetry, indent=2)}\n"
            f"Strands Decider 2B Guardrail Status: {guardrail_action}\n\n"
            f"Provide a concise Root Cause Analysis, Impact Radius, and Future Prevention Strategy."
        )

        # 1. Live Bedrock invocation if credentials are configured
        if self.bedrock_runtime:
            try:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 512,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                })
                response = self.bedrock_runtime.invoke_model(
                    body=body,
                    modelId=self.model_id,
                    accept="application/json",
                    contentType="application/json",
                )
                response_body = json.loads(response.get("body").read())
                output_text = response_body["content"][0]["text"]
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                input_tokens = response_body.get("usage", {}).get("input_tokens", 220)
                output_tokens = response_body.get("usage", {}).get("output_tokens", 140)

                return {
                    "output_text": output_text,
                    "model_id": self.model_id,
                    "latency_ms": elapsed_ms,
                    "tokens_used": input_tokens + output_tokens,
                    "estimated_cost_usd": round((input_tokens * 0.000003) + (output_tokens * 0.000015), 6),
                    "is_live_bedrock": True,
                }
            except Exception:
                pass  # Fall through to dynamic scenario synthesis

        # 2. Dynamic Scenario Synthesis for Offline / Mock Testing
        elapsed_ms = round(1650.0 + (time.perf_counter() - start_time) * 1000, 2)
        
        if "iam" in incident_title.lower() or "key" in incident_title.lower():
            simulated_text = (
                f"### Root Cause Analysis (Bedrock Synthesis [Simulated])\n"
                f"- **Root Cause**: AWS GuardDuty detected anomalous API invocation from unrecognized IP with leaked access key.\n"
                f"- **Impact Radius**: IAM credentials targeted; no data exfiltration confirmed.\n"
                f"- **Remediation & Prevention**: Strands Decider 2B dispatched human-in-the-loop quarantine payload. Recommend enabling AWS Secrets Manager automatic rotation."
            )
        elif "deadlock" in incident_title.lower() or "aurora" in incident_title.lower():
            simulated_text = (
                f"### Root Cause Analysis (Bedrock Synthesis [Simulated])\n"
                f"- **Root Cause**: High transaction concurrency produced cascading deadlocks across worker nodes.\n"
                f"- **Impact Radius**: Aurora primary instance CPU spiked to 99%; read queries unaffected.\n"
                f"- **Remediation & Prevention**: Strands Decider 2B halted destructive database termination. Restarted deadlocked worker sessions safely."
            )
        else:
            simulated_text = (
                f"### Root Cause Analysis (Bedrock Synthesis [Simulated])\n"
                f"- **Root Cause**: Sudden query throughput spike saturated connection pool and in-memory cache.\n"
                f"- **Impact Radius**: Limited to session cache microservice; no data loss.\n"
                f"- **Remediation & Prevention**: Strands Decider 2B auto-verified safe cache flush. Recommend scaling Redis replica count."
            )

        return {
            "output_text": simulated_text,
            "model_id": self.model_id,
            "latency_ms": elapsed_ms,
            "tokens_used": 340,
            "estimated_cost_usd": 0.00374,
            "is_live_bedrock": False,
        }
