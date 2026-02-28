# Sentinel Bank — AI-Powered Banking System

A full-stack banking backend powered by FastAPI, PostgreSQL, and AI agents for fraud detection, complaint routing, and financial personalization.

---

### AI-Driven Agents

| Agent                | Role                                                       |
| -------------------- | ---------------------------------------------------------- |
| **Sentinel Agent**   | Real-time Fraud/Risk assessment for every transaction      |
| **Dispatcher Agent** | Routes complaints using AI sentiment & priority analysis   |
| **Trajectory Agent** | AI-Powered financial advisor & spending future-forecasting |

### Core Banking Features

- **Authentication**: JWT-based login with OTP verification and Magic Link support.
- **Transactions**: Secure internal transfers with database-level locking and risk scoring.
- **Reporting**: Ability to report failed transactions and track status via unique IDs.
- **Profile**: Full user profile management, security preferences, and theme settings.

---

## Tech Stack

| Layer         | Technology                         |
| ------------- | ---------------------------------- |
| API Framework | FastAPI (Python)                   |
| Database      | PostgreSQL on Aiven (cloud-hosted) |
| ORM           | SQLAlchemy (async)                 |
| AI Agents     | LangChain + LangGraph              |
| Auth          | JWT (Jose) + bcrypt                |
| Vector Store  | ChromaDB (RAG pipeline)            |

---

## Project Structure

```
Sentinnel_bank_project/
├── Backend/               ← API layer (endpoints, models, auth)
│   ├── app.py             ← Main FastAPI app
│   ├── api.py             ← Auth routes
│   ├── models.py          ← SQLAlchemy DB models
│   ├── schemas.py         ← Pydantic request/response schemas
│   ├── database.py        ← Async DB connection
│   ├── middleware.py      ← JWT token guard
│   └── auth.py            ← Password hashing & JWT helpers
│
├── app/
│   ├── agents/            ← AI agents (sentinel, dispatcher, trajectory)
│   ├── prompts/           ← LLM system prompts
│   └── core/              ← LangGraph orchestrator
│
├── database/
│   ├── create_schema.py   ← Creates all DB tables on Aiven
│   └── README.md          ← Database setup guide
│
├── WORK_DISTRIBUTION.md   ← Team task assignments
├── ONBOARDING.md          ← Setup guide for new teammates
├── .env.example           ← Environment variable template
└── requirements.txt       ← Python dependencies
```

---

## Getting Started

### 1. Clone and set up environment

```bash
git clone https://github.com/Cunyie08/genai_sentinel_banking_integration.git
cd genai_sentinel_banking_integration

python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in your credentials (get from TunjiPaul privately):

- `DB_PASSWORD` — Aiven database password
- `DATABASE_URL` — Full asyncpg connection string
- `SECRET_KEY` — JWT signing key

### 3. Run the server

```bash
# Start the backend server
python -m Backend.app
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Database

16 tables on Aiven PostgreSQL. See [`database/README.md`](database/README.md) for the full schema and setup instructions.

---

## Team

| Person             | Role                                            |
| ------------------ | ----------------------------------------------- |
| **[TunjiPaul](https://github.com/tunjipaul)** | Database Schema + Auth + User Profile endpoints |
| **[Mr Opnex](https://github.com/opnex)** | Accounts + Cards + Notifications                |
| **[Halimat](https://github.com/halimahAkinoso)** | Transactions (Extended) + Settings              |
| **[Barrister Femi](https://github.com/Femilearnsai)** | Quick Services + Admin + Audit                  |
| **[David Ekpo](https://github.com/david4129)** | Backend Foundation + Trajectory Agent           |

See [`WORK_DISTRIBUTION.md`](WORK_DISTRIBUTION.md) for full task breakdown and [`ONBOARDING.md`](ONBOARDING.md) for setup instructions.
