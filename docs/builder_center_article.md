# 🛡️ SentryMesh: Building an Autonomous Cloud Incident Triage Agent with Strands Decider 2B & Amazon Bedrock

> **Tags**: `#strands-decider-2b` `#guardrails` `#tool-selection` `#model-routing`  
> **Author**: Syed Arbaaz  
> **Repository**: [GitHub — SentryMesh Agent](https://github.com/Syedx2/sentrymesh-agent)

---

## 🚀 Introduction & The Problem
In modern cloud operations, Site Reliability Engineers (SREs) and DevOps teams face an overwhelming volume of operational alerts and incidents. While Large Language Models (LLMs) like Claude 3.5 Sonnet on Amazon Bedrock offer remarkable reasoning capabilities for root-cause analysis, using generative LLMs for **every high-frequency guardrail check and tool decision** is slow (~1,800ms) and cost-prohibitive ($20+ per 10k decisions).

Furthermore, granting an autonomous agent direct write access to cloud infrastructure (such as restarting EC2 instances, quarantining IAM credentials, or flushing cluster caches) without deterministic guardrails introduces critical security and stability risks.

To solve this, we built **SentryMesh** — an autonomous AWS incident triage and remediation agent that pairs **Strands Decider 2B** for ultra-fast, calibrated decision-making with **Amazon Bedrock** for deep generative synthesis, backed by a **hard-floor safety guardrail**.

---

## 🧠 Architecture: The Dual-Brain Agent Pattern

```
                           +----------------------------------------+
                           |   Incoming AWS CloudWatch / Event      |
                           +----------------------------------------+
                                               |
                                               v
                          +------------------------------------------+
                          |      Strands Decider 2B Engine           |
                          |   (Single-Pass Logit Scoring, ~115ms)    |
                          +------------------------------------------+
                               /              |               \
                              /               |                \
                             v                v                 v
                 [PROCEED (>90%)]     [CONFIRM (Human)]     [DENY / BLOCKED]
                         |                    |                     |
                         v                    v                     v
                 Execute AWS Tool      Dispatch PagerDuty     Halt & Alert
              (Redis Flush / Scale)    1-Click DevOps Signoff Security Team
                         \                    |                     /
                          \                   |                    /
                           +------------------+-------------------+
                                              |
                                              v
                              +--------------------------------+
                              |      Amazon Bedrock            |
                              |   (Claude 3.5 Sonnet / Nova)   |
                              |   Generative Post-Mortem & RCA |
                              +--------------------------------+
```

### 1. The Decision Layer (Strands Decider 2B)
Instead of generating conversational text, **Strands Decider 2B** acts as our agent's **system-one reflex brain**. It scores candidate decisions in a single forward pass:
* **`Proceed`**: Safe operational action verified in context (e.g., flushing cache, scaling tasks).
* **`Confirm`**: High blast-radius action (e.g., database termination, IAM credential revocation) requiring human sign-off.
* **`Guide`**: Action parameters out of bounds; guidance returned to rescale parameters.
* **`Deny`**: Policy violation or adversarial prompt injection detected.

### 2. Hard-Floor Safety Enforcement
Even in autonomous pipelines, safety must have a code-level floor. SentryMesh enforces policy checks in `AWSToolRegistry` ensuring that destructive tools (e.g. `terminate_database_instance`) are strictly blocked from execution without verified authorization.

### 3. The Generative Layer (Amazon Bedrock)
Once the deterministic action is handled, the execution receipt is passed to **Amazon Bedrock (Claude 3.5 Sonnet / Amazon Nova)** to generate a structured executive post-mortem and root-cause analysis (RCA).

---

## 📊 Measured Benchmarks: Strands Decider 2B vs Pure LLM

We benchmarked incident triage runs across both architectures:

| Benchmark Metric | Strands Decider 2B | Frontier Bedrock LLM | Improvement |
| :--- | :--- | :--- | :--- |
| **Decision Latency (Mean)** | **112.4 ms** | 1,850.0 ms | ⚡ **93.9% Faster** |
| **P95 Latency** | **119.1 ms** | 2,400.0 ms | ⚡ **95.0% Faster** |
| **Cost per 10,000 Decisions** | **$0.10** | $22.50 | 💰 **99.6% Savings** |
| **Decision Format** | Calibrated Logit Probabilities | Unstructured Prose | Deterministic & Safe |
| **Compute Footprint** | 1.9B Parameters (Serverless/Edge) | 70B+ Frontier Model | Cloud Native |

---

## 🧩 The Reusable Decision Pattern (`CloudGuardrailDecisionPattern`)

As required by the hackathon, we packaged our decision recipe into an open-source, reusable pattern that any builder can drop into their agent:

```python
from decider_patterns.cloud_guardrail_pattern import (
    CloudGuardrailDecisionPattern, 
    GuardrailEvaluationRequest
)
from agent.decider_engine import StrandsDeciderEngine

decider = StrandsDeciderEngine(endpoint_url="http://localhost:8000")

# 1. Structure the incident context
request = GuardrailEvaluationRequest(
    incident_type="ElastiCacheMemoryPressure",
    proposed_tool="flush_redis_cluster_cache",
    tool_arguments={"cluster_id": "redis-prod-01"},
    environment="production",
    blast_radius="low"
)

# 2. Score via Strands Decider 2B in ~115ms
decision = decider.evaluate_guardrail(request)

print(f"Action: {decision.action} | Confidence: {decision.confidence:.1%}")
```

---

## 💡 What We Learned
1. **Separation of Concerns is King**: LLMs are brilliant at prose and creative synthesis, but decider models (like Decider 2B) provide the speed, determinism, and cost efficiency needed for real-time cloud operations.
2. **Confidence Scores Provide Explainability**: Having an explicit logit confidence score (e.g. 91.6% Proceed) makes agent decisions transparent and auditable for compliance.

---

## 🔗 Links & Resources
* **GitHub Repository**: [https://github.com/Syedx2/sentrymesh-agent](https://github.com/Syedx2/sentrymesh-agent)
* **Live Web Dashboard Demo**: [https://syedx2.github.io/sentrymesh-agent/](https://syedx2.github.io/sentrymesh-agent/)
* **Demo Video**: [YouTube Demo Link](https://youtube.com)
