"""
=============================================================================
SentryMesh Agent End-to-End Test Suite
=============================================================================
"""

import json
from agent.sentry_agent import SentryMeshAgent, IncidentPayload


def test_agent_pipeline():
    agent = SentryMeshAgent()

    test_incidents = [
        IncidentPayload(
            title="ElastiCache Memory Spike (>92%)",
            service="Redis-SessionCache",
            severity="P2-High",
            environment="production",
            proposed_remediation_tool="flush_redis_cluster_cache",
            tool_arguments={"cluster_id": "cache-prod-primary"},
            telemetry={"memory_used_mb": 14720, "max_memory_mb": 16000, "evictions_sec": 420},
        ),
        IncidentPayload(
            title="Compromised IAM Access Key Detected via GuardDuty",
            service="AWS IAM",
            severity="P1-Critical",
            environment="production",
            proposed_remediation_tool="quarantine_compromised_iam_key",
            tool_arguments={"access_key_id": "AKIAIOSFODNN7EXAMPLE", "account_id": "123456789012"},
            telemetry={"threat_type": "UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration"},
        ),
        IncidentPayload(
            title="Database Latency Deadlock",
            service="Aurora PostgreSQL",
            severity="P1-Critical",
            environment="production",
            proposed_remediation_tool="terminate_database_instance",
            tool_arguments={"db_instance_id": "aurora-db-01"},
            telemetry={"active_deadlocks": 14, "cpu_pct": 99.4},
        ),
    ]

    print("\n" + "=" * 70)
    print("  SENTRYMESH AUTONOMOUS INCIDENT TRIAGE PIPELINE EXECUTION")
    print("=" * 70)

    for idx, inc in enumerate(test_incidents, 1):
        print(f"\n[Test Case {idx}] Incident: {inc.title}")
        print(f"Service: {inc.service} | Severity: {inc.severity} | Proposed Tool: {inc.proposed_remediation_tool}")
        
        result = agent.triage_incident(inc)

        print(f"-> Strands Decider 2B Decision : {result.decider_action} (Confidence: {result.decider_confidence_pct}) in {result.decider_latency_ms}ms")
        print(f"-> Candidate Scores            : {result.decider_candidate_scores}")
        print(f"-> Execution Status            : {result.status}")
        print(f"-> Total Pipeline Latency      : {result.total_pipeline_latency_ms}ms")
        print(f"-> Cost Savings vs Pure LLM    : {result.cost_savings_vs_pure_llm_pct}%")
        print(f"-> Bedrock Synthesis Preview   : {result.bedrock_synthesis.get('output_text', '')[:100]}...\n")
        print("-" * 70)


if __name__ == "__main__":
    test_agent_pipeline()
