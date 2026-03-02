# Prompt Layer - Sentinel Banking AI

This directory contains structured system prompts for each agent.

Prompts are:

- Schema-aligned
- Governance-restricted
- Non-decision-making

---

## Prompts

### dispatcher_prompt.py
Used by DispatcherAgent.
Ensures routing explanation remains aligned with policy.

---

### sentinel_prompt.py
Used by SentinelAgent.
Ensures fraud explanations remain policy-grounded.

---

### trajectory_prompt.py
Used by TrajectoryAgent.
Ensures eligibility explanations comply with PRS-001.

---

## Governance Rule

Prompts explicitly instruct:

- Do NOT override decisions.
- Do NOT invent thresholds.
- Return JSON only.
- Follow response schema strictly.

---

## Design Principle

Decision logic lives in deterministic engines.
LLM layer exists for explanation only.