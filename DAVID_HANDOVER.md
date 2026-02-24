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
- **Webhook Security**: Inbound emails are protected by **Svix Signature Verification**. This ensures that ONLY real emails from Resend are processed, preventing hackers from "spoofing" customer complaints or attacking your AI API limits.
- **OTP & Password Reset**: Sent via email with a 15-minute expiration for enhanced security.

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

### 3. Production-Grade Webhook Security

- **Signature Verification**: Uses Svix to validate payloads at the `/webhooks/inbound-email` endpoint.
- **Non-Blocking Architecture**: Leverages FastAPI `BackgroundTasks` to process AI routing without slowing down the initial HTTP response.

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

**Happy Coding, David! 🚀**
