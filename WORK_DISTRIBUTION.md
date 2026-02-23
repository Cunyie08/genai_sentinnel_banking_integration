# Sentinel Bank — Work Distribution

## Team

| Person             | Focus Area                         |
| ------------------ | ---------------------------------- |
| **TunjiPaul**      | Schema + Auth + User Profile       |
| **Mr Opnex**       | Accounts + Cards + Notifications   |
| **Halimat**        | Transactions (Extended) + Settings |
| **Barrister Femi** | Quick Services + Admin + Audit     |
| **David Ekpo**     | Trajectory Agent                   |

---

## 📅 Timeline

| Day       | Date                | Goal                                                                  |
| --------- | ------------------- | --------------------------------------------------------------------- |
| **Day 1** | Sunday, 23 Feb 2026 | Environment setup, branch creation, start building assigned endpoints |
| **Day 2** | Monday, 24 Feb 2026 | Complete all endpoints, open PRs into `backend`, final integration    |

> [!IMPORTANT]
> All PRs must be open and ready for review by end of **Day 2 (24 Feb)**.

---

> [!IMPORTANT]
> Read the `ONBOARDING.md` file first if you are new to the project.

### Environment Setup

```bash
# Copy env template and fill in credentials shared by TunjiPaul
cp .env.example .env
```

Fill in: `DB_PASSWORD`, `DATABASE_URL`, `SECRET_KEY` — get these privately from TunjiPaul.

### Branch Workflow

```bash
# Branch off David Ekpo's backend branch
git checkout backend
git pull origin backend
git checkout -b feature/your-feature-name
```

Open a Pull Request into **`backend`** when done — not `master`.  
The final `backend` → `master` merge will be done by TunjiPaul once everything is integrated.

### Async Rule — No Exceptions

```python
@app.get("/your-endpoint")
async def your_endpoint(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)   # on protected routes only
):
    result = await db.execute(select(YourModel).filter(...))
    return result.scalars().first()
```

- All functions → `async def`
- All DB calls → `await`
- Use `AsyncSession`, never sync `Session`
- Use `Backend/app.py` as your template

---

## Already Built — Do Not Duplicate

| Endpoint                            | File             |
| ----------------------------------- | ---------------- |
| `POST /auth/register`               | `Backend/api.py` |
| `POST /auth/token` (login)          | `Backend/api.py` |
| `POST /auth/refresh`                | `Backend/api.py` |
| `POST /auth/forgot-password` (stub) | `Backend/api.py` |
| `POST /customers`                   | `Backend/app.py` |
| `POST /make_transaction`            | `Backend/app.py` |
| `POST /make_complaint`              | `Backend/app.py` |

---

## 👤 TunjiPaul — Schema + Auth + User Profile

**Database Schema** (`database/create_schema.py` + `Backend/models.py`):

- Add missing tables: `otp_tokens`, `refresh_tokens`, `password_reset_tokens`, `biometric_credentials`, `voice_credentials`, `notifications`, `cards`, `user_settings`, `chat_sessions`, `chat_messages`, `fraud_alerts`, `transaction_verifications`, `service_transactions`, `audit_logs`
- Add corresponding SQLAlchemy model classes to `Backend/models.py`
- Run `python database/create_schema.py` to apply to Aiven

**Auth Endpoints** (`Backend/api.py`):

- `POST /auth/logout`
- `POST /auth/verify-otp`
- `POST /auth/resend-otp`
- `PATCH /auth/change-password`
- `POST /auth/reset-password`
- `POST /auth/forgot-password` ← replace existing stub with real email sending

**User Profile Endpoints** (`Backend/app.py`):

- `GET /users/me`
- `PATCH /users/update-profile`
- `PATCH /users/update-preferences`
- `GET /users/{userId}` (admin)
- `DELETE /users/{userId}` (admin)

---

## 👤 Mr Opnex — Accounts + Cards + Notifications

**Branch:** `feature/accounts-cards-notifications` (off `backend`)

**Accounts** (`Backend/app.py`):

- `GET /accounts`
- `GET /accounts/{accountId}`
- `GET /accounts/{accountId}/balance`
- `GET /accounts/{accountId}/status`
- `PATCH /accounts/{accountId}/freeze`
- `PATCH /accounts/{accountId}/activate`

**Cards** (new file `Backend/cards.py`):

- `GET /cards`
- `POST /cards/request`
- `PATCH /cards/{cardId}/freeze`
- `PATCH /cards/{cardId}/activate`
- `GET /cards/{cardId}/details`
- `POST /cards/{cardId}/set-limit`

**Notifications** (new file `Backend/notifications.py`):

- `GET /notifications`
- `POST /notifications/send`
- `PATCH /notifications/{id}/read`
- `DELETE /notifications/{id}`

> [!NOTE]
> Add models for `cards` and `notifications` to `Backend/models.py`.  
> Register your routers in `Backend/app.py` with `app.include_router(your_router)`.

---

## 👤 Halimat — Transactions (Extended) + Settings

**Branch:** `feature/transactions-settings` (off `backend`)

**Extended Transactions** (`Backend/app.py`):

- `GET /transactions`
- `GET /transactions/{transactionId}`
- `GET /transactions/account/{accountId}`
- `GET /transactions/filter` (date, amount, type as query params)
- `GET /transactions/{transactionId}/status`
- `POST /transactions/report-failed`
- `POST /transactions/internal-transfer`

**Settings** (new file `Backend/settings_routes.py`):

- `GET /settings`
- `PATCH /settings/update-theme`
- `PATCH /settings/update-language`
- `PATCH /settings/update-notifications`
- `PATCH /settings/update-security`

> [!NOTE]
> Settings reads/writes to the `user_settings` table (TunjiPaul will create it).  
> Register your settings router in `Backend/app.py`.

---

## 👤 Barrister Femi — Quick Services + Admin + Audit

**Branch:** `feature/services-admin-audit` (off `backend`)

**Quick Services** (new file `Backend/services.py`):

- `POST /services/airtime/purchase`
- `GET /services/airtime/providers`
- `POST /services/data/purchase`
- `GET /services/data/providers`
- `POST /services/bills/pay`
- `GET /services/bills/categories`
- `GET /services/bills/providers`

**Admin Dashboard** (new file `Backend/admin.py`):

- `GET /admin/users`
- `GET /admin/users/{userId}`
- `GET /admin/users/{userId}/transactions`
- `GET /admin/users/{userId}/complaints`
- `PATCH /admin/users/{userId}/status`
- `GET /admin/tickets`
- `PATCH /admin/tickets/{ticketId}/assign`
- `PATCH /admin/tickets/{ticketId}/resolve`
- `GET /admin/analytics/transactions`
- `GET /admin/analytics/fraud`
- `GET /admin/analytics/user-growth`

**Audit & Logging** (new file `Backend/audit.py`):

- `GET /audit/logs`
- `GET /audit/user/{userId}`
- `GET /audit/transaction/{transactionId}`

> [!NOTE]
> All Admin endpoints must check `user.role == "admin"` before returning data — reject with 403 if not.  
> Log all admin actions to the `audit_logs` table (TunjiPaul will create it).

---

## 👤 David Ekpo — Trajectory Agent

David is working on the **Trajectory Agent** (`app/agents/trajectory_agent.py`) and its associated personalization endpoints.

---

## File Reference

| File                    | Purpose                                      |
| ----------------------- | -------------------------------------------- |
| `Backend/app.py`        | Main app — register all routers here         |
| `Backend/models.py`     | Add new SQLAlchemy models here               |
| `Backend/schemas.py`    | Add Pydantic input/output schemas here       |
| `Backend/database.py`   | DB connection — do not modify                |
| `Backend/middleware.py` | `get_current_user` — protects routes         |
| `Backend/auth.py`       | JWT + bcrypt helpers                         |
| `app/agents/`           | AI agents (sentinel, dispatcher, trajectory) |
