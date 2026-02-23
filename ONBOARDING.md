# Sentinel Bank — Onboarding Guide

### For: Mr Opnex, Halimat, Barrister Femi

---

## What Is This Project?

**Sentinel Bank** is an AI-powered banking backend. It combines a standard banking API (accounts, transactions, complaints) with three AI agents:

| Agent                | What It Does                                                                                            |
| -------------------- | ------------------------------------------------------------------------------------------------------- |
| **Sentinel Agent**   | Fraud detection — scores every transaction for risk                                                     |
| **Dispatcher Agent** | Complaint routing — reads a complaint and routes it to the right department with priority and sentiment |
| **Trajectory Agent** | Personalization — analyzes spending habits and gives financial advice (David Ekpo's work)               |

The backend is built with **FastAPI** (Python web framework) and talks to a **PostgreSQL database hosted on Aiven** (a cloud database).

---

## Project Structure

```
Sentinnel_bank_project/
├── Backend/               ← The API layer (your main working area)
│   ├── app.py             ← Main FastAPI app — all routes are here or registered here
│   ├── api.py             ← Auth routes (register, login, token)
│   ├── models.py          ← Database table definitions (SQLAlchemy)
│   ├── schemas.py         ← Request/response data shapes (Pydantic)
│   ├── database.py        ← DB connection — DO NOT MODIFY
│   ├── middleware.py      ← Token checker for protected routes
│   └── auth.py            ← JWT + password hashing helpers
│
├── app/
│   ├── agents/            ← AI agents (sentinel, dispatcher, trajectory)
│   ├── prompts/           ← AI system prompts
│   └── core/              ← LangGraph orchestrator
│
├── database/
│   └── create_schema.py   ← Script that creates all DB tables on Aiven
│
├── .env                   ← Your local credentials (NEVER commit this)
├── .env.example           ← Template showing what .env should look like
└── requirements.txt       ← Python dependencies
```

---

## How the Backend Works (Simple)

### When a user registers:

1. They send `POST /auth/register` with email + password
2. Backend checks if they exist in the `customers` table (they must be an existing bank customer)
3. Creates a `users` record with a hashed password
4. Returns a `user_id`

### When a user logs in:

1. They send their email + password to `POST /auth/token`
2. Backend verifies password → returns a **JWT token** (a temporary key)
3. User sends this token in the header of every future request

### When a user makes a request to a protected endpoint:

1. The token is checked by `get_current_user` (in `middleware.py`)
2. If valid → the endpoint runs
3. If missing or expired → `401 Unauthorized`

### Transaction flow (example of how agents are used):

1. User sends `POST /make_transaction`
2. Backend verifies token → confirms account belongs to user
3. Sends transaction to **Sentinel Agent** → gets fraud risk score
4. If risk > 80% → blocks transaction
5. If safe → saves to DB, deducts balance

---

## Environment Setup

### 1. Clone the repo and set up Python environment

```bash
git clone https://github.com/Cunyie08/genai_sentinel_banking_integration.git
cd genai_sentinel_banking_integration

python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Mac/Linux

pip install -r requirements.txt
```

### 2. Set up your `.env`

```bash
cp .env.example .env
```

Then open `.env` and fill in the values TunjiPaul will share with you privately:

```
DB_PASSWORD=<get from TunjiPaul>
DATABASE_URL=<get from TunjiPaul>
SECRET_KEY=<get from TunjiPaul>
```

> [!CAUTION]
> Never commit `.env` to GitHub. It is already in `.gitignore`.

---

## The Async Pattern — You Must Follow This

FastAPI + the database driver are **asynchronous**. This means every endpoint function must use `async def` and every database call must use `await`.

**Template to copy for every endpoint you write:**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from Backend.database import get_db
from Backend.middleware import get_current_user
from Backend.models import Account   # whichever model you need

router = APIRouter(tags=["Your Tag"])

@router.get("/your-endpoint")
async def your_function(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)   # remove this for public endpoints
):
    result = await db.execute(
        select(Account).filter(Account.customer_id == user.customer_id)
    )
    accounts = result.scalars().all()
    return accounts
```

**Key rules:**

- ✅ Always `async def`
- ✅ Always `await db.execute(...)`
- ✅ Always `AsyncSession`, not `Session`
- ✅ `get_current_user` on every protected route
- ❌ Never use regular sync `psycopg2` or blocking calls inside endpoints

Look at `Backend/app.py` for working examples of this pattern.

---

## How to Add New Endpoints

### Option A — Add to `Backend/app.py` directly

For account or transaction endpoints, add them directly into `app.py` following the existing pattern.

### Option B — Create a new file with a router

For a new module (e.g. cards, notifications), create a new file:

```python
# Backend/cards.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.database import get_db
from Backend.middleware import get_current_user

router = APIRouter(prefix="/cards", tags=["Cards"])

@router.get("/")
async def get_cards(db: AsyncSession = Depends(get_db), user = Depends(get_current_user)):
    ...
```

Then register it in `Backend/app.py`:

```python
from Backend.cards import router as cards_router
app.include_router(cards_router)
```

---

## Adding New DB Models

If your endpoints need a new table (e.g. `cards`), add its SQLAlchemy model to `Backend/models.py`:

```python
class Card(Base):
    __tablename__ = "cards"

    card_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(50), ForeignKey("accounts.account_id", ondelete="CASCADE"))
    card_type: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[Optional[str]] = mapped_column(String(20), default="active")

    account: Mapped["Account"] = relationship(back_populates="cards")
```

> [!NOTE]
> TunjiPaul will add the SQL table definitions to `create_schema.py`. You just need to add the corresponding model class in `models.py` to use it in your endpoints.

---

## Branch Workflow

```bash
# 1. Start from David Ekpo's backend branch
git checkout backend
git pull origin backend

# 2. Create your feature branch
git checkout -b feature/your-feature-name

# 3. Do your work, then commit
git add .
git commit -m "describe what you did"

# 4. Push and open a PR into backend
git push origin feature/your-feature-name
```

Open a Pull Request on GitHub → **base: `backend`** (not master).  
TunjiPaul will handle the final `backend` → `master` merge.

---

## Questions?

Contact **TunjiPaul** or **David Ekpo** — they are both fully briefed on the existing codebase.
