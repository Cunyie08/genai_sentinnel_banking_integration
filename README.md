# Sentinnel Banking Platform

Branch: `final_backend_integrations`

This branch delivers an end-to-end integration of the AI-enabled banking backend (FastAPI) with the React frontend, plus governance-focused agent orchestration (Sentinel, Dispatcher, Trajectory), RAG grounding, and operational modules such as admin, notifications, cards, settings, and audit.

## Branch Status

- Active branch: `final_backend_integrations`
- Latest branch commit at time of documentation: `7393c7b`
- Scope versus `master`: large integration branch with backend + frontend consolidation and AI workflow wiring.

## Architecture At A Glance

- `Backend/`: FastAPI API surface, auth, user profile, transactions, quick services, admin, cards, notifications, settings, and audit modules.
- `app/`: AI/ML orchestration stack (agents, orchestrator, RAG system, prompts, utils, data loaders).
- `Frontend/`: React + Vite customer web application.
- `database/`: database notes and schema setup guidance.
- `docs/architecture.svg`: architecture diagram.

## Core Capabilities In This Branch

1. Authentication and account-linked user access
- JWT login, OTP verification flow, password reset/change endpoints.
- Middleware-based protected routes and role checks (including admin-only operations).

2. AI-assisted banking workflows
- `SentinelAgent`: fraud assessment for transaction scenarios.
- `DispatcherAgent`: complaint routing, priority and sentiment classification.
- `TrajectoryAgent`: product recommendation flows for eligible users.

3. Customer operations
- Profile and preference updates.
- Account listing, balances, status, freeze/activate actions.
- Transaction listing, filtering, status checks, failure reporting.
- Internal transfer endpoint with fraud check gate.

4. Quick services and operational modules
- Airtime, data, bills, and internal transfer under `/services`.
- Cards lifecycle endpoints under `/cards`.
- Notifications under `/notifications`.
- Settings controls under `/settings`.
- Admin control-plane endpoints under `/admin`.
- Audit trail access under `/audit`.

5. Frontend integration
- React app with protected routes (`/dashboard`, `/history`, `/transfer`, etc.).
- Axios client with JWT auto-attach and 401 redirect handling.
- Configurable backend URL via `VITE_API_URL`.

## Quick Start

### Prerequisites

- Python 3.11+ (3.13 currently used in project artifacts)
- Node.js 20+
- PostgreSQL (Aiven or compatible)

### 1) Clone and install backend dependencies

```bash
git clone <repo-url>
cd Sentinnel_bank_project
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2) Configure backend environment

Create `.env` from `.env.example` and fill:

- `DATABASE_URL`
- `SECRET_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `RESEND_API_KEY`
- `RESEND_WEBHOOK_SECRET`

### 3) Run backend

```bash
python -m Backend.app
```

Backend default runtime in this branch:
- Host: `127.0.0.1`
- Port: `8080`

Health check:
- `GET http://127.0.0.1:8080/health`

### 4) Install and run frontend

```bash
cd Frontend
npm install
npm run dev
```

Optional frontend env (`Frontend/.env`):

```bash
VITE_API_URL=http://127.0.0.1:8080
```

## API Module Map

- Auth: `/auth/*` from `Backend/api.py`
- Core app and agent flows: `Backend/app.py`
- Quick services: `/services/*`
- Admin: `/admin/*`
- Audit: `/audit/*`
- Cards: `/cards/*`
- Notifications: `/notifications/*`
- Settings: `/settings/*`

Use interactive API docs when backend is running:
- `http://127.0.0.1:8080/docs`

## Frontend Route Map

Public:
- `/onboarding`
- `/signup`
- `/verify-otp`
- `/login`
- `/forgot-password`

Protected:
- `/dashboard`
- `/history`
- `/transfer`
- `/cards`
- `/services`
- `/profile`
- `/notifications`
- `/settings`

## Branch-Specific Risks / Notes

- Root `README.md` previously had unresolved merge conflict markers. This has now been replaced with a clean document.
- Several generated/binary artifacts exist in-branch (for example `Frontend/node_modules`, RAG/chroma files, model binary). Keep release packaging and CI filtering in mind.
- Some legacy docs may refer to older run commands or old folder layouts. Prefer this README and `docs/BRANCH_final_backend_integrations.md`.

## Additional Branch Documentation

For a deeper branch dossier (diff summary, integration notes, merge checklist), see:

- `docs/BRANCH_final_backend_integrations.md`

## Team Notes

This branch integrates contributions from backend, AI, and frontend workflows. For handover context, refer to:

- `DAVID_HANDOVER.md`
- `STANDUP_REPORT_2026_02_27.md`
- `COMPLETE_ME.md`
