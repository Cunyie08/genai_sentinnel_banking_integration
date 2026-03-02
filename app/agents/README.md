# Agents Layer - Sentinel Banking AI System

This directory contains all autonomous decision-making agents in the Sentinel Banking AI architecture.

Each agent is responsible for a distinct banking workflow and operates under strict governance rules.

---

## Overview

The agents layer implements a hybrid architecture:

- Deterministic rule engine
- Policy-grounded RAG validation
- Structured LLM explanation layer (non-overriding)

Agents never override policy logic. The LLM layer is used strictly for explanation and audit traceability.

---

## Agents

### 1. Abstract Agent (`abstract_agent.py`)
Base class defining the standard interface:

- `async run(payload: Dict[str, Any])`
- Structured response contract
- Enforced consistency across agents

---

### 2. Dispatcher Agent (`dispatcher_agent.py`)
Responsible for complaint routing.

Functions:
- Classifies customer complaints
- Routes to correct department (TSU, FRM, COC, etc.)
- Applies SLA logic
- Generates audit-ready explanation

Uses:
- RAG policy grounding
- Keyword + semantic routing

---

### 3. Sentinel Agent (`sentinel_agent.py`)
Fraud risk assessment engine.

Functions:
- Computes fraud risk score (0–100)
- Applies policy thresholds
- Determines block / challenge / approve
- Generates governance-safe explanation

Architecture:
- Deterministic fraud scoring
- Behavioral Feature Engineering
- ML Fraud Probability
- Policy Risk Scoring
- Channel Risk Assessment
- LLM explanation layer

---

### 4. Trajectory Agent (`trajectory_agent.py`)
Product recommendation & eligibility engine.

Functions:
- Proactive product recommendation
- Policy validation (PRS-001 compliance)
- DSR (Debt Service Ratio) evaluation
- Structured LLM explanation

Architecture:
- Deterministic recommendation engine
- RAG policy validation
- Structured explanation layer

---

## Governance Rules

- Agents do NOT override policy.
- LLMs do NOT make decisions.
- Deterministic engines own eligibility and risk.
- All outputs are structured and logged.

---

## Design Principles

- Separation of decision and explanation
- Policy-first architecture
- Audit traceability
- Async-compatible
- Production-grade error handling

---

## Execution

Agents are not meant to run independently in production.
They are invoked via the Orchestrator (see `/core`).