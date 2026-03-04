# Core Layer - Sentinnel Banking Orchestration

This directory contains the system control plane.

It is responsible for:

- Request routing
- Agent orchestration
- Graph-based execution flow
- System logging
- Error handling

---

## Components

### 1. Orchestrator (`orchestrator.py`)

The central entry point for all requests.

Responsibilities:

- Receives structured requests
- Routes requests via SystemGraph
- Invokes appropriate agent
- Logs system events
- Returns final structured response

Supported request types:

{
  "type": "complaint" | "transaction" | "recommendation",
  ...
}

---

### 2. System Graph (`graph.py`)

Defines routing logic between request types and agents.

Example mapping:

complaint → DispatcherAgent  
transaction → SentinelAgent  
recommendation → TrajectoryAgent  

This abstraction allows future multi-step workflows.

---

## Architectural Philosophy

The core layer does NOT:

- Contain business logic
- Make eligibility decisions
- Compute fraud risk

It strictly coordinates system execution.

---

## Flow

main.py  
→ Orchestrator  
→ Graph Resolution  
→ Agent Execution  
→ Logging + Metrics  
→ Structured Response  

---

## Design Goals

- Decoupled routing logic
- Expandable multi-agent pipelines
- Centralized error handling
- Production-grade logging
