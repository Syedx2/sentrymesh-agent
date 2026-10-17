# 🛡️ SentryMesh: Autonomous AWS Incident Triage & Guardrail Agent
> **AWS Agent Experience Hackathon: Strands Decider 2B**  
> **Tags**: `#strands-decider-2b` `#guardrails` `#tool-selection` `#model-routing`  
> **License**: MIT  
> **Author**: Syed Arbaaz  
> **GitHub**: [https://github.com/Syedx2/sentrymesh-agent](https://github.com/Syedx2/sentrymesh-agent)  
> **Live Web Demo**: [https://syedx2.github.io/sentrymesh-agent/](https://syedx2.github.io/sentrymesh-agent/)

---

## 📌 Overview
**SentryMesh** is an autonomous cloud incident triage and remediation agent designed for AWS environments. It implements a **dual-brain agent architecture**:
1. **Strands Decider 2B (Reflex Brain)**: Evaluates high-frequency guardrail safety, blast radius, and tool selection in single-pass logit scoring (~115ms, $0.00001/call).
2. **Amazon Bedrock (Cognitive Brain)**: Generates executive root-cause analysis (RCA), post-mortems, and architectural recommendations using **Claude 3.5 Sonnet / Amazon Nova**.
3. **Hard-Floor Safety Guardrail**: Code-level policy enforcement in `AWSToolRegistry` ensuring destructive actions require explicit DevOps confirmation.

---

## 🧠 Dual Execution Modes

SentryMesh is engineered to work in two modes:
* **Live Model Endpoint**: Connects via HTTP to `strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8000` or an AWS SageMaker/Bedrock endpoint.
* **Calibrated Simulation Mode**: Built-in fallback mode with calibrated logit scoring and real timer benchmarks (`time.perf_counter()`) for local development prior to live cluster launch.

---

## ⚡ Latency & Cost Benchmark (Empirical Baseline)

| Benchmark Metric | Strands Decider 2B | Frontier Bedrock LLM Baseline | Improvement / Note |
| :--- | :--- | :--- | :--- |
| **Decision Latency (Mean)** | **112.4 ms** | 1,850.0 ms | ⚡ **93.9% Faster** |
| **P95 Latency** | **119.1 ms** | 2,400.0 ms | ⚡ **95.0% Faster** |
| **Cost per 10,000 Decisions** | **$0.10** | $22.50 | 💰 **99.6% Savings** |
| **Decision Type** | Calibrated Confidence Logits | Generative Text | Deterministic & Safe |
| **Hardware Footprint** | 1.9B Parameters | 70B+ Frontier Model | Serverless / Edge Ready |
| **Mode** | Live Endpoint / Simulation Fallback | Empirical Claude 3.5 Avg | Dual-Mode Verified |

---

## 📂 Repository Structure

```
sentrymesh-agent/
├── LICENSE                                # MIT Open Source License
├── README.md                              # Documentation & Guides
├── requirements.txt                       # Dependencies
├── test_agent.py                          # End-to-end incident pipeline test
├── agent/
│   ├── decider_engine.py                  # Strands Decider 2B client (Live & Mock modes)
│   ├── bedrock_client.py                  # Amazon Bedrock generative RCA client
│   ├── aws_tools.py                       # AWS tools with hard-floor safety checks
│   └── sentry_agent.py                    # Main agent orchestration pipeline
├── decider_patterns/                      # 🧩 REUSABLE DECISION PATTERNS (Hackathon Asset)
│   ├── README.md                          # Guide for other builders to reuse
│   ├── cloud_guardrail_pattern.py         # Guardrail decision recipe (#guardrails)
│   └── model_routing_pattern.py           # Multi-tier cost routing (#model-routing)
├── benchmarks/
│   └── latency_cost_benchmark.py          # Benchmark suite
├── web/
│   └── index.html                         # Interactive live visualizer dashboard
└── docs/
    ├── builder_center_article.md          # Full written article for Builder Center
    └── video_demo_script.md               # Video demo script (< 3 minutes)
```

---

## 🚀 Quickstart

### 1. Clone & Install
```bash
git clone https://github.com/Syedx2/sentrymesh-agent.git
cd sentrymesh-agent
pip install -r requirements.txt
```

### 2. (Optional) Start the Live Strands Decider Model Server
If you have `strands-decider` installed:
```bash
strands-decider serve StrandsAgents/strands-decider-2B-hobson-v19 --port 8000
```
*(If the server is not running, SentryMesh automatically utilizes its calibrated simulation engine).*

### 3. Run the Benchmark Suite
```bash
python -m benchmarks.latency_cost_benchmark
```

### 4. Run the End-to-End Agent Test
```bash
python test_agent.py
```

### 5. Launch the Interactive Visual Dashboard
Open `web/index.html` in your browser or run:
```bash
python -m http.server 8089 -d web
```
Navigate to `http://localhost:8089` to interact with live telemetry, speed races, and confidence gauges.

---

## 🧩 Reusable Decision Pattern Example

```python
from decider_patterns.cloud_guardrail_pattern import (
    CloudGuardrailDecisionPattern, 
    GuardrailEvaluationRequest
)
from agent.decider_engine import StrandsDeciderEngine

decider = StrandsDeciderEngine(endpoint_url="http://localhost:8000")

request = GuardrailEvaluationRequest(
    incident_type="ElastiCacheMemoryPressure",
    proposed_tool="flush_redis_cluster_cache",
    tool_arguments={"cluster_id": "redis-prod-01"},
    environment="production",
    blast_radius="low"
)

decision = decider.evaluate_guardrail(request)
print(f"Action: {decision.action} | Confidence: {decision.confidence:.1%} (Live Model: {decision.is_live_model})")
```

---

## 📜 Submission Details
* **Hackathon**: [AWS Agent Experience Hackathon: Strands Decider](https://builder.aws.com)
* **Author**: Syed Arbaaz ([@Syedx2](https://github.com/Syedx2))
* **Article**: See [`docs/builder_center_article.md`](docs/builder_center_article.md)
