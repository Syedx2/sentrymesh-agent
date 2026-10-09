# 🎬 SentryMesh Demo Video Script (< 3 Minutes)
> **Goal**: Fulfill the hackathon qualification requirement by demonstrating the agent working live, highlighting the **Strands Decider 2B decision firing with its confidence score**, and showcasing the reusable pattern.

---

### ⏱️ Timeline & Script Breakdown

#### 0:00 – 0:35 | Introduction & The Problem
* **Visual**: Show SentryMesh dashboard or Architecture Slide.
* **Speaker**: 
  > "Hi everyone, I'm Syed Arbaaz, and this is **SentryMesh** — an autonomous AWS incident triage and remediation agent built for the AWS Agent Experience Hackathon. 
  > When production alerts fire in AWS, standard LLMs are too slow (~2 seconds) and expensive for high-frequency guardrail decisions. SentryMesh pairs **Strands Decider 2B** as our ultra-fast reflex brain with **Amazon Bedrock** for deep generative post-mortems."

#### 0:35 – 1:30 | Live Demo: Incident 1 (Autonomous Remediation with High Confidence)
* **Visual**: Trigger `ElastiCache Memory Pressure (>92%)` in the UI / Terminal.
* **Action**:
  * Point to the **Strands Decider 2B Decision Output**.
  * Highlight the **Confidence Score (91.6% Proceed)** and **Decision Latency (116ms)**.
* **Speaker**:
  > "Here, our Redis cluster is hitting 92% memory usage. The agent considers executing `flush_redis_cluster_cache`. 
  > Strands Decider 2B evaluates the blast radius and fires a **Proceed decision with 91.6% calibrated confidence in just 116 milliseconds**. 
  > The AWS tool executes immediately, resolving the alert without human intervention."

#### 1:30 – 2:15 | Live Demo: Incident 2 (Human-in-the-Loop Escalation)
* **Visual**: Trigger `Critical Database Deadlock — Terminate RDS Instance`.
* **Action**:
  * Show Decider 2B output: **Confirm (75.5% confidence)**.
  * Show status: `ESCALATED_FOR_APPROVAL`.
* **Speaker**:
  > "Now watch what happens with a destructive action: terminating an RDS Aurora cluster. 
  > Strands Decider 2B recognizes the critical blast radius and fires a **Confirm decision with 75.5% confidence**. 
  > Rather than blindly executing, it pauses and routes a 1-click confirmation payload to DevOps on-call."

#### 2:15 – 2:45 | The Reusable Decision Pattern & Bedrock Post-Mortem
* **Visual**: Show `decider_patterns/cloud_guardrail_pattern.py` code & Bedrock Root-Cause Analysis output.
* **Speaker**:
  > "After every incident, Amazon Bedrock synthesizes the root-cause analysis and executive summary. 
  > We've packaged this into a reusable open-source decision pattern in `decider_patterns/` that any AWS builder can drop directly into their own agent. 
  > In our benchmarks, moving decisions to Strands Decider 2B reduced decision latency by **93.9%** and slashed costs by **99.6%**."

#### 2:45 – 3:00 | Conclusion & Wrap Up
* **Visual**: Show GitHub repo and Builder Center article summary.
* **Speaker**:
  > "Check out the public GitHub repository linked below to try the reusable pattern today. Thank you AWS Builder Center team!"

---

### 📋 Checklist for Recording
- [ ] Record in 1080p HD.
- [ ] Show the confidence score (e.g. `91.6%`) clearly visible on screen.
- [ ] Keep total video length under 2 minutes 50 seconds.
- [ ] Upload to YouTube as Public or Unlisted.
