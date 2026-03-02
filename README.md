# Sentinnel Banking

## Executive Summary

Sentinel Banking is a multi-agent artificial intelligence system designed to enhance operational efficiency, risk management, and customer experience within a digital banking environment.

The system automates three core banking functions:

| Agent                | Function                                        |
| -------------------- | ----------------------------------------------- |
| **Dispatcher Agent** | Complaint classification & department routing   |
| **Sentinel Agent**   | Evaluates transactions using a hybrid model that| 
|                      | combines machine learning with policy-based risk| 
|                      | controls and channel-aware safeguards.          |
| **Trajectory Agent** | Recommends eligible financial products based on |
|                      | structured eligibility rules, affordability     |
|                      | checks, and policy validation.                  |

Sentinel Banking is built with a governance-first architecture. Decision-making is handled by deterministic engines and structured rules. Machine learning enhances fraud detection but does not override policy safeguards. Language models are used strictly to generate clear, audit-ready explanations, not to make financial decisions.

Key characteristics of the system include:

- Policy-aligned decision frameworks
- Hybrid fraud detection (machine learning + rule-based controls)
- Channel-aware risk assessment
- Structured logging for audit traceability
- Modular multi-agent orchestration

All data used in development is synthetic and designed to simulate real banking workflows without exposing sensitive information.
Sentinel Banking demonstrates how artificial intelligence can be deployed responsibly within financial systems; balancing automation, explainability, and governance.


# 1. Overview

## Multi-Agent AI System for Intelligent Banking Operations

Sentinel Banking is a modular multi-agent AI system designed to automate core banking workflows using deterministic logic, machine learning, and policy-grounded reasoning.

The system is structured around three operational domains:

* Complaint Routing
* Fraud Detection
* Product Recommendation

It combines structured decision engines with governance-safe explanation layers.

---

# 2. System Architecture

![Architecture](docs/architecture.svg)

---

# 3. Core Design Philosophy

Sentinel Banking is built on a layered architecture:

1. Deterministic Decision Engines
2. Machine Learning (Fraud Probability)
3. Policy Grounding via RAG
4. Schema-Constrained LLM Explanations
5. Structured Logging

LLMs do not make decisions.
They explain decisions made by deterministic engines.

---

# 4. Agents

## Dispatcher Agent

Purpose: Complaint classification and department routing.

* Semantic + keyword routing
* SLA classification
* Department mapping
* Policy-grounded explanation

---

## Sentinel Agent

Purpose: Fraud risk scoring and action mapping.

Sentinel uses a hybrid fraud architecture:

### Fraud Pipeline

Transaction
→ Behavioral Feature Engineering
→ ML Fraud Probability
→ Policy Risk Scoring
→ Channel Risk Assessment
→ Final Risk Score
→ Action (Approve / Challenge / Block)

### ML Integration

The fraud model:

* Learns behavioral transaction patterns
* Outputs `ml_probability`
* Detects anomalies beyond static rules
* Contributes to hybrid risk score

### Channel Risk Layer

After ML scoring, Sentinel evaluates transaction channel:

* ATM
* POS
* Web
* Mobile

Channel context can escalate actions even when ML probability is moderate.

This ensures channel-aware fraud governance.

---

## Trajectory Agent

Purpose: Product recommendation and eligibility validation.

Trajectory uses:

* Deterministic recommendation engine
* Loan signal score thresholds
* DSR validation (33.3% cap)
* Policy validation via RAG
* Structured LLM explanation

It does not rely on ML.

---

# 5. RAG Policy Engine

The system uses:

* ChromaDB
* SentenceTransformers embeddings
* Policy chunk retrieval
* Grounded validation

RAG is used to validate:

* Complaint routing categories
* Product eligibility compliance

RAG does not override deterministic logic.

---

# 6. Machine Learning Component

ML is integrated only in the Sentinel Agent.

Model outputs:

* Fraud probability (0-1)

Used to:

* Enhance anomaly detection
* Influence hybrid risk scoring
* Improve fraud sensitivity

Final decision remains policy-controlled.

---

# 7. Logging & Traceability

Every agent decision is logged in structured JSON format:

* reasoning.log
* system.log

Each entry includes:

* Timestamp
* Agent name
* Full decision payload

This enables audit traceability.

---

# 8. Project Structure

```
app/
├── agents/
├── core/
├── dataset/
├── evaluation/
├── logs/
├── prompts/
├── rag/
├── utils/
```

---

# 9. Technology Stack

* Python 3.13
* AsyncIO
* ChromaDB
* SentenceTransformers
* OpenAI API
* Gemini API
* Pydantic
* Structured logging

---

# 10. Synthetic Data Engine

Synthetic datasets include:

* Customers
* Accounts
* Transactions
* Complaints

Used to simulate:

* Behavioral fraud patterns
* Loan signal scoring
* Eligibility scenarios

No real customer data is used.

---

# 11. Running the System

```bash
python -m main
```

Supported request types:

```json
{
  "type": "complaint",
  "complaint_id": "..."
}
```

```json
{
  "type": "transaction",
  "transaction_id": "..."
}
```

```json
{
  "type": "recommendation",
  "customer_id": "..."
}
```

---

# 12. Meet the Team

### AI Engineers

* Kanyisola Fagbayi
* Blessing James
* David Ekpo
* Hassan Majaro

### AI Developers

* Tunji Paul Ogor
* Reuben Mulero
* Itunu Bisayo
* Opeyemi Thomas
* Halimah Akinoso

---

# Summary

Sentinel Banking demonstrates and reflects a modular, explainable approach to intelligent banking automation through:

* Multi-agent orchestration
* Hybrid ML + deterministic fraud detection
* Policy-grounded validation
* Channel-aware risk assessment
* Governance-safe explanation architecture
* Structured audit logging




