# Branch Documentation: `db-branch`

Last updated: 2026-03-04

## 1. Branch Intent

`db-branch` is a backend-focused integration branch centered on:

- Core banking API implementation with FastAPI and async SQLAlchemy.
- AI-assisted transaction risk and complaint routing workflows.
- Operational modules (admin, audit, cards, notifications, settings, services).
- A frontend simulator app in `Frontend/sentinel-bank` for UI exploration.

This document is the branch handover and review guide.

## 2. Branch Metadata

- Branch: `db-branch`
- HEAD at documentation time: `afc3498`
- Remote: `origin/db-branch`

Recent relevant commits:

1. `afc3498` power
2. `129a8b0` added githubs of backend devs
3. `17b3438` Docs: Force-add David's Technical Handover notes
4. `dd06c3e` Docs: Update README with new features and finalize handover notes
5. `9a62b02` Refactor: cleanup and transaction endpoint updates

## 3. Repository Layout (db-branch)

```text
Sentinnel_bank_project/
  Backend/                     # FastAPI app and modular routers
  app/                         # Agents, orchestration, prompts, utilities
  Frontend/sentinel-bank/      # React + Redux + Vite simulator frontend
  database/                    # DB setup notes and schema helpers
  README.md                    # Root project overview
  requirements.txt             # Python dependencies
```

## 4. Runtime Architecture

### 4.1 Backend

Entrypoint:

```bash
python -m Backend.app
```

Runtime in code:

- Host: `127.0.0.1`
- Port: `8080`

Health endpoint:

- `GET /health`

### 4.2 Frontend

Project path:

- `Frontend/sentinel-bank`

Commands:

```bash
cd Frontend/sentinel-bank
npm install
npm run dev
```

Notes:

- This frontend uses Redux (`@reduxjs/toolkit`, `react-redux`).
- Current UI is simulator/terminal style (`MobileSimulator`, `GlassBoxTerminal`).

## 5. Backend API Surface

### 5.1 Router modules and prefixes

- `Backend/api.py`: authentication endpoints (`/auth/*`)
- `Backend/services.py`: `/services/*`
- `Backend/admin.py`: `/admin/*`
- `Backend/audit.py`: `/audit/*`
- `Backend/cards.py`: `/cards/*`
- `Backend/notifications.py`: `/notifications/*`
- `Backend/settings_routes.py`: `/settings/*`
- `Backend/app.py`: profile/accounts/transactions/core endpoints

### 5.2 Key direct app endpoints

- `GET /`
- `GET /health`
- `POST /make_complaint`
- `POST /customers`
- `POST /make_transaction`
- `GET /accounts`
- `GET /accounts/{accountId}`
- `GET /transactions`
- `GET /transactions/filter`
- `POST /transactions/internal-transfer`

Swagger/OpenAPI:

- `http://127.0.0.1:8080/docs`

## 6. Configuration

Create `.env` from `.env.example` and set:

- `DATABASE_URL`
- `SECRET_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `RESEND_API_KEY`
- `RESEND_WEBHOOK_SECRET`

Also available in `.env.example`:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_SSL`

## 7. Core Functional Areas in db-branch

1. Authentication
- Register/login, OTP verification and token lifecycle.

2. Customer profile and preferences
- User profile retrieval/update.
- Security/language/theme/notification preference updates.

3. Transactions and account controls
- Transaction posting and history retrieval.
- Internal transfers with fraud checks.
- Account status and balance operations.

4. Complaints and routing
- Complaint capture and AI-assisted routing flow.

5. Admin and operations
- Admin views, ticket actions, analytics.
- Audit log querying.
- Cards, notifications, settings, quick services.

## 8. Verification Checklist (Local)

1. Backend startup:
```bash
python -m Backend.app
```
Expect `/health` to return `status: ok`.

2. Frontend startup:
```bash
cd Frontend/sentinel-bank
npm run dev
```
Confirm app renders both simulator and terminal panels.

3. API sanity checks:
- Auth flow: register, login/token.
- Account list and transaction list for seeded user.
- `POST /transactions/internal-transfer` success and failure paths.
- Admin and audit endpoints with role-appropriate token.

## 9. Known Caveats

1. Root README has some encoding artifacts in this branch (special characters rendered incorrectly in some terminals).
2. This branch is backend-heavy; frontend is a focused simulator and not a full retail banking route-based app.
3. Verify secrets and database URLs before sharing branch snapshots.

## 10. Recommended Next Docs

1. `docs/API_REFERENCE_db-branch.md` with request/response examples per endpoint group.
2. `docs/DEPLOYMENT_db-branch.md` for staging/production startup and env strategy.
3. `docs/TEST_PLAN_db-branch.md` for endpoint and integration regression checklist.
