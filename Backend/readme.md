🚀 Tech Stack
Framework: FastAPI

Database & ORM: PostgreSQL (via asyncpg), SQLAlchemy 2.0 (Async)

Data Validation: Pydantic V2

Authentication: JWT (JSON Web Tokens) & Bcrypt password hashing

AI Integration: OpenAI (gpt-4o) & Google GenAI (gemini-2.5-flash)

🗄️ Database Architecture
The system utilizes a strictly typed relational database with VARCHAR(50) string-based primary keys (e.g., CUST-..., ACCT-..., TXN-...) for system-wide consistency.

Customers: The core identity (CIF). Holds demographic data, BVN, NIN, and contact info.

Accounts: Financial entities linked to Customers. Features 10-digit auto-generated account numbers and Numeric(18,2) precise balances.

Users: The online authentication profile. Linked 1-to-1 with a Customer. Stores login email and hashed passwords.

Transactions: The immutable ledger. Records debits/credits and stores real-time AI fraud risk scores.

Complaints: Customer support tickets. Asynchronously updated by AI to determine routing department and urgency.

⚙️ Local Setup & Installation
Clone the repository and install dependencies:

Bash
pip install -r requirements.txt
Environment Variables (.env):
Create a .env file in the root directory:

Code snippet
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/your_db_name
SECRET_KEY=your_super_secret_jwt_key
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
Run the Server:

Bash
uvicorn Backend.api:app --reload
Swagger UI Documentation will be available at: http://localhost:8000/docs

🔐 Authentication Flow
Important Business Logic: A user cannot register for an online profile unless they already exist in the customers table with an active bank account.

1. POST /auth/register
   Creates an online user profile and securely links it to their core banking Customer ID based on their email.

Payload: ```json
{
"email": "customer@example.com",
"password": "securepassword123"
}

Response: 200 OK (Returns user_id and success message). 403 Forbidden if no matching customer account exists.

2. POST /auth/token
   Logs the user in and generates a JWT.

Payload: multipart/form-data (Standard OAuth2 username/password form. Note: Pass the email into the username field).

Response:

JSON
{
"access_token": "eyJhbGciOiJIUzI1NiIs...",
"token_type": "bearer"
}
💰 Core Banking Endpoints
All endpoints below are Protected and require the JWT token in the Authorization: Bearer <token> header.

POST /make_transaction
Processes a debit or credit, automatically adjusts account balances safely using Python Decimal, and runs a synchronous AI Fraud check before committing.

AI Integration: Uses SentinelAgent. If the calculated risk_score is > 0.8, the transaction is blocked.

Payload:

JSON
{
"account_number": "1234567890",
"channel": "mobile app",
"device_id": "Device-XYZ",
"counterparty_bank": "Access Bank",
"narration": "Groceries",
"transaction_type": "debit",
"amount": 5000.00,
"currency": "NGN",
"merchant_category": "supermarket",
"merchant_name": "GrabNGO"
}
Response: 200 OK

JSON
{
"status": "approved",
"transaction_reference": "REF-A1B2C3D4E5",
"fraud_analysis": {
"risk_score": 0.1,
"reasoning": "Standard grocery transaction, consistent with user behavior."
}
}
POST /make_complaint
Logs a customer complaint. Returns immediately to the user while spinning up a Background Task for the AI to analyze the text.

AI Integration: Uses DispatcherAgent to run asynchronously. It reads the complaint_text and automatically updates the database row with the correct department, priority, and sentiment.

Payload:

JSON
{
"account_number": "1234567890",
"linked_transaction_id": "",
"linked_reference": "",
"complaint_channel": "mobile_app",
"complaint_text": "I transferred money to my friend but he hasn't received it yet."
}
(Note: Empty strings for optional IDs are handled safely by the backend).

Response: 200 OK

JSON
{
"message": "Complaint submitted successfully and is being routed.",
"complaint_id": "CMP-X9Y8Z7A6B5"
}

### ⚡ Quick Services

Located in `Backend/services.py`, these endpoints allow users to perform utility transactions.

- **Airtime & Data**: Purchase top-ups for any major Nigerian telco (MTN, Airtel, Glo, 9mobile).
- **Bill Payments**: Pay for Electricity (IKEDC/EKEDC), Water, and Cable TV (DSTV/GOtv).
- **Business Logic**: Automatically verifies account ownership and debits the `current_balance`.

### 🛡️ Admin Dashboard

Located in `Backend/admin.py`, restricted to users with `role == "admin"`.

- **User Management**: View profiles, transaction histories, and update user status (active/suspended).
- **Ticket Management**: Assign and resolve customer complaints.
- **Analytics**: High-level views of transaction volumes, fraud alert stats, and user growth.

### 📜 Audit & Logging

Integrated into all administrative actions and located in `Backend/audit.py`.

- **Immersion**: Every status change or ticket resolution is logged to the `audit_logs` table.
- **Transparency**: Admins can query logs by specific user or transaction IDs to investigate issues.

🧠 AI Agents Architecture
The AI layer is abstracted into agent classes located in the /agents directory. They utilize a fallback mechanism: if OpenAI is rate-limited, they automatically fall back to Google Gemini.

SentinelAgent: Evaluates transaction payloads against strict JSON schemas to output fraud likelihood and reasoning traces.

DispatcherAgent: Evaluates natural language customer complaints to classify intent and route tickets to specific bank departments (e.g., Card Services, Operations, Fraud).

Backend Developer Notes
Datetimes: PostgreSQL expects offset-naive timestamps. The codebase enforces datetime.now(timezone.utc).replace(tzinfo=None) to maintain UTC accuracy without crashing the asyncpg driver.

Database Sessions: Background tasks (process_complaint_routing) must instantiate their own SessionLocal scope, as the primary request's session closes immediately upon returning the HTTP response.

## 🚀 Future Scalability Roadmap

As the system grows, the following architectural upgrades are planned to ensure high performance and reliability:

1. **Message Broker (Apache Kafka)**: To move from a monolithic request-response model to a highly scalable event-driven architecture.
2. **Distributed Task Queue (FastAPI + Celery)**: Transition from standard `BackgroundTasks` to Celery to handle heavy AI processing loads outside the main application process.
3. **Caching & Logging (Redis)**: Implement Redis as a high-speed caching layer to significantly reduce response latency and as a centralized hub for real-time logging and session management.
