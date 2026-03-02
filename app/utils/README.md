 # Utilities Layer - Sentinnel Banking AI

This directory contains reusable system utilities.

---

## Components

### llm_client.py
Unified abstraction over OpenAI and Gemini models.

Features:
- Structured schema enforcement
- Async support
- Fallback handling
- Rate limit resilience

---

### logger.py
Provides:

- ReasoningLogger
- SystemLogger

Ensures structured logging across the system.

---

### schemas/
Contains Pydantic models for:

- Dispatcher responses
- Sentinel responses
- Trajectory responses

Used to enforce strict JSON outputs.

---

## Design Goals

- Reusable components
- Schema safety
- Async compatibility
- Production readiness
