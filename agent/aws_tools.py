"""
=============================================================================
AWS Tool Registry & Operational Action Handlers
=============================================================================
Deterministic cloud tools executed by the agent after Strands Decider 2B
guardrail verification.
Enforces a hard-coded security floor regardless of model output.
"""

import time
import uuid
from typing import Dict, Any


class AWSToolRegistry:
    """
    Registry of AWS operational tools with blast-radius definitions and
    hard-coded security enforcement.
    """

    TOOLS_CATALOG = {
        "flush_redis_cluster_cache": {
            "description": "Flushes ElastiCache Redis keys to clear corrupted in-memory cache.",
            "default_blast_radius": "low",
            "requires_confirmation": False,
        },
        "scale_ecs_autoscaling_group": {
            "description": "Increases ECS task desired count to absorb traffic surges.",
            "default_blast_radius": "medium",
            "requires_confirmation": False,
        },
        "quarantine_compromised_iam_key": {
            "description": "Attaches an explicit DenyAll IAM inline policy to deactivate leaked access keys.",
            "default_blast_radius": "medium",
            "requires_confirmation": True,
        },
        "reboot_ec2_instance": {
            "description": "Performs a graceful reboot of an unresponsive EC2 instance.",
            "default_blast_radius": "high",
            "requires_confirmation": True,
        },
        "terminate_database_instance": {
            "description": "Terminates an RDS Aurora cluster instance (Destructive).",
            "default_blast_radius": "critical",
            "requires_confirmation": True,
        },
    }

    @classmethod
    def execute_tool(cls, tool_name: str, args: Dict[str, Any], confirmed: bool = False) -> Dict[str, Any]:
        """
        Executes the cloud operational tool and returns execution receipts.
        HARD-FLOOR SAFETY: If tool catalog specifies `requires_confirmation=True`,
        execution is strictly rejected unless `confirmed=True` is provided.
        """
        start_time = time.perf_counter()
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"

        if tool_name not in cls.TOOLS_CATALOG:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in registered AWS tools catalog.",
                "execution_id": execution_id,
                "status": "TOOL_NOT_FOUND",
            }

        tool_meta = cls.TOOLS_CATALOG[tool_name]

        # Hard-floor security check: Prevent unauthorized destructive execution
        if tool_meta.get("requires_confirmation") and not confirmed:
            return {
                "success": False,
                "error": f"Hard security guardrail: Tool '{tool_name}' requires explicit human DevOps confirmation.",
                "execution_id": execution_id,
                "status": "BLOCKED_BY_SAFETY_FLOOR",
                "requires_human_approval": True,
            }

        # Simulated cloud action latency
        elapsed_ms = round((time.perf_counter() - start_time) * 1000 + 35.0, 2)

        return {
            "success": True,
            "tool_name": tool_name,
            "execution_id": execution_id,
            "parameters": args,
            "status": "SUCCESSFULLY_APPLIED",
            "execution_latency_ms": elapsed_ms,
            "message": f"AWS operational action '{tool_name}' executed cleanly.",
        }
