# Evaluation Layer - Sentinnel Banking AI

This directory contains performance tracking utilities.

Important distinction:

Model confidence ≠ System evaluation.

---

## Components

### metrics.py

Provides lightweight performance indicators such as:

- confidence tracking
- error occurrence
- eligibility distribution

---

### llm_evaluation.py

Optional evaluation layer for:

- explanation quality scoring
- hallucination detection
- policy alignment validation

---

## Purpose

The evaluation layer allows:

- Performance monitoring
- Drift detection
- System benchmarking
- Audit reporting

---

## Design Principle

Evaluation is separate from decision logic.

Agents produce decisions.
Evaluation measures performance over time.
