# 🧩 Reusable Strands Decider 2B Decision Patterns
> Tagged: `#strands-decider-2b` `#guardrails` `#model-routing` `#tool-selection`

This directory contains production-ready, reusable decision recipes that any builder can drop directly into their own AWS AI agents.

---

## 📦 Available Patterns

### 1. `CloudGuardrailDecisionPattern` (`#guardrails`, `#tool-selection`)
* **File:** `cloud_guardrail_pattern.py`
* **Purpose:** Evaluates whether an agent's proposed cloud infrastructure action is safe, grounded, or requires human DevOps approval.
* **Decision Outputs:** `Proceed`, `Guide`, `Confirm`, `Deny`.
* **Latency:** ~115ms (Single forward pass).

#### How to use in your agent:
```python
from decider_patterns.cloud_guardrail_pattern import (
    CloudGuardrailDecisionPattern, 
    GuardrailEvaluationRequest
)
from agent.decider_engine import StrandsDeciderEngine

decider = StrandsDeciderEngine()

# 1. Prepare the evaluation request
request = GuardrailEvaluationRequest(
    incident_type="HighMemorySpike",
    proposed_tool="reboot_ec2_instance",
    tool_arguments={"instance_id": "i-09a8b7c6d5e4f3a21", "force": False},
    environment="production",
    blast_radius="medium",
)

# 2. Score via Strands Decider 2B
decision = decider.evaluate_guardrail(request)

print(f"Decision: {decision.action} ({decision.confidence:.1%}) in {decision.decision_latency_ms}ms")
if decision.action == "Proceed":
    # Execute safe tool
    pass
elif decision.action == "Confirm":
    # Route to DevOps Slack / PagerDuty for human approval
    pass
```

---

### 2. `ModelRoutingDecisionPattern` (`#model-routing`, `#policy`)
* **File:** `model_routing_pattern.py`
* **Purpose:** Acts as an ultra-fast API gateway traffic cop. Decides whether to route queries to Instant Cache, Deterministic Lambda Tool, Amazon Bedrock Generative LLM, or Security Block.
* **Cost Savings:** ~85% reduction in Bedrock token consumption.

#### How to use in your agent:
```python
from decider_patterns.model_routing_pattern import ModelRoutingDecisionPattern
from agent.decider_engine import StrandsDeciderEngine

decider = StrandsDeciderEngine()
route_decision = decider.evaluate_route("Show me current CPU utilization of RDS cluster")

if route_decision.destination == "AWSActionTool":
    # Fast direct CloudWatch fetch (~40ms, $0 LLM cost)
    pass
elif route_decision.destination == "AmazonBedrockLLM":
    # Invoke Bedrock Claude 3.5 Sonnet for deep generative synthesis
    pass
```

---

## 🛠️ Integration with Strands InterventionHandler
If you use the official `strands-agents` Python framework, wire the decision pattern into the agent lifecycle:

```python
from strands import Agent
from strands.interventions import InterventionHandler, Proceed, Deny, Confirm

class SentryGuardrailHandler(InterventionHandler):
    def before_tool_call(self, event):
        decision = decider.evaluate_guardrail_from_event(event)
        if decision.action == "Proceed":
            return Proceed()
        elif decision.action == "Confirm":
            return Confirm(prompt="High blast radius requires human signoff.")
        return Deny(reason=decision.reasoning)
```
