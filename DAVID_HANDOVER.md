# 🏦 Sentinel Bank - Technical Handover for David

Welcome to the backend of Sentinel Bank! This document outlines the core architecture, security protocols, and a complete guide on how to test every endpoint using the **Swagger UI**.

---

## 🏗️ System Architecture

### 1. Database Layer

- **PostgreSQL (Aiven Cloud)**: 16-table schema including Customers, Accounts, Transactions, Complaints, and Security Tokens.
- **ORM**: SQLAlchemy (Async) with Pydantic for data validation.

### 2. AI Routing Intelligence

- **Dispatcher Agent**: Located in `app/agents/dispatcher_agent.py`.
- **Logic**: Automatically classifies incoming complaints by **Department**, **Priority**, and **Sentiment**.
- **Fallback**: Uses OpenAI (GPT-4o) → Gemini (2.0-Flash) → Keyword Heuristics (Simulation).

### 3. Communication Loop

- **Inbound**: Webhook at `/webhooks/inbound-email` receives customer messages.
- **Outbound**: Integration with **Resend API** to send premium HTML emails for OTPs, Password Resets, and Complaint Confirmations.

---

## 🔐 Security Protocols

- **JWT Authentication**: Most endpoints require a Bearer Token in the header.
- **Robust Error Handling**: Added `try-except` blocks to the authentication flow to prevent server crashes on malformed password salts (Bcrypt errors).
- **Webhook Security**: Inbound emails are protected by **Svix Signature Verification**.
- **OTP & Password Reset**: Sent via email with a 15-minute expiration for enhanced security.
- **Transaction Locking**: Internal transfers use `with_for_update()` to prevent race conditions and ensure data integrity.

---

## ⭐ Key Features Implemented

### 1. Advanced AI Complaint Dispatcher

- **Multi-LLM Integration**: Seamlessly switches between OpenAI and Google Gemini based on key availability.
- **Intelligent Classification**: Dissects user intent to assign a specific **Department Code**, **Priority Level** (Low/Medium/High), and **Sentiment Score**.
- **Transparency**: Logs detailed agent reasoning to `app/logs/reasoning.log` for debugging and auditing.

### 2. High-Fidelity Communication Engine

- **Branded HTML Experience**: Replaced plain-text emails with premium, CSS-styled templates for a trustworthy banking experience.
- **Automated Workflows**:
  - **Registration**: Auto-sends 6-digit OTPs.
  - **Security**: Secure, token-based "Forgot Password" flow.
  - **Support**: Instant "Complaint Received" auto-replies with Ticket IDs.

### 3. Sentinel-First Transactions

- **Risk Scoring**: Every `POST /make_transaction` and `POST /transactions/internal-transfer` call triggers the **Sentinel Agent**.
- **Real-time Blocking**: Transactions with a risk score > 0.8 are automatically blocked.
- **Reporting**: Users can track transaction status and report failed ones via new dedicated endpoints.

### 4. Codebase Health & Refactor

- **Dependency Audit**: The `requirements.txt` has been fully updated with core libraries (`fastapi`, `bcrypt`, `uvicorn`, etc.).
- **Comment Cleanup**: Removed redundant "stub" comments and placeholder sections across the entire backend for a production-ready look.
- **Unified Logic**: Consolidated auth and transaction logic to ensure high security and reliability.

---

## ️ Maintenance & Logs

- **AI Reasoning**: Check `app/logs/reasoning.log` to see exactly why the AI routed a complaint to a specific department.
- **Server**: Run using `python -m Backend.app`.

---

## 🌐 Production Deployment

When deploying to a live server (e.g., Render, Railway, AWS):

### 1. Configure Resend Webhook

1. Go to your **Resend Dashboard** > **Webhooks**.
2. Add a new webhook pointing to: `https://your-live-api.com/webhooks/inbound-email`.
3. Copy the **Signing Secret**.

### 2. Environment Variables

Ensure the following are set in your production `.env`:

- `RESEND_WEBHOOK_SECRET`: The signing secret from the step above.
- `RESEND_API_KEY`: Your production Resend API key.
- `DATABASE_URL`: Your production PostgreSQL connection string.

### 3. Verification

Once deployed, the backend will **strictly** verify every incoming webhook. If the secret is missing or incorrect, it will return a `401 Unauthorized` for security.

---

## 🚀 Roadmap & Scalability

Looking ahead, we've identified key areas to ensure the bank can scale to millions of users:

- **Kafka Integration**: Transition to an event-driven architecture for high-throughput transaction processing.
- **Celery + Redis**: Replace `BackgroundTasks` with a dedicated worker pool (Celery) and a high-speed caching/messaging layer (Redis) to minimize latency and manage asynchronous AI operations more effectively.

---

**Happy Coding, David! 🚀**
