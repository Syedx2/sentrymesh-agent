"""
=============================================================================
Amazon Bedrock Generative Synthesis Client
=============================================================================
Connects with Amazon Bedrock (Claude 3.5 Sonnet / Amazon Nova) for deep
generative reasoning and root-cause analysis when handed off by Strands Decider 2B.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger("BedrockAgentClient")


class BedrockAgentClient:
    """
    Client for invoking Amazon Bedrock foundation models with telemetry.
    Supports environment variable override via BEDROCK_MODEL_ID.
    """

    DEFAULT_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
    FALLBACK_MODEL_ID = os.getenv("BEDROCK_FALLBACK_MODEL_ID", "us.amazon.nova-lite-v1:0")

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
        except NoCredentialsError:
            logger.info("AWS credentials not found. Bedrock client running in simulation mode.")
            self.bedrock_runtime = None
        except Exception as e:
            logger.info(f"Bedrock client not initialized ({e}). Running in simulation mode.")
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
            candidates = [self.model_id]
            if self.FALLBACK_MODEL_ID and self.FALLBACK_MODEL_ID != self.model_id:
                candidates.append(self.FALLBACK_MODEL_ID)

            for candidate_model in candidates:
                try:
                    response = self.bedrock_runtime.converse(
                        modelId=candidate_model,
                        messages=[{"role": "user", "content": [{"text": prompt}]}],
                        inferenceConfig={"maxTokens": 512, "temperature": 0.2},
                    )
                    output_text = response["output"]["message"]["content"][0]["text"]
                    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    usage = response.get("usage", {})
                    input_tokens = usage.get("inputTokens", 220)
                    output_tokens = usage.get("outputTokens", 140)

                    return {
                        "output_text": output_text,
                        "model_id": candidate_model,
                        "latency_ms": elapsed_ms,
                        "tokens_used": input_tokens + output_tokens,
                        "estimated_cost_usd": round((input_tokens * 0.000003) + (output_tokens * 0.000015), 6),
                        "is_live_bedrock": True,
                    }
                except ClientError as e:
                    logger.debug(f"Bedrock invocation failed for {candidate_model}: {e}")
                except Exception as e:
                    logger.debug(f"Unexpected Bedrock error for {candidate_model}: {e}")

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
