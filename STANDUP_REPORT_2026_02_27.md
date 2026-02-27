SENTINEL BANK - DETAILED TECHNICAL STAND-UP REPORT
Date: February 27, 2026
Status: Phase 1-5 Implementation 100% Complete

CORE ARCHITECTURE AND STACK
The backend is built as a highly modular FastAPI application with an asynchronous database layer.

- Framework: FastAPI (Uvicorn runner, Pydantic V2 validation).
- Database: PostgreSQL (Aiven Cloud) using SQLAlchemy 2.0 (AsyncSession) and Asyncpg.
- AI Logic: LangGraph orchestrator with support for OpenAI (GPT-4o) and Google Gemini (2.0 Flash) fallbacks.
- Communications: Resend API for transactional emails and Svix for secure webhook signature verification.

ENDPOINT STRUCTURES AND MODELS

1. Authentication Layer (router: auth_router)

- POST /auth/register: Uses UserCreate schema. Validates email unique constraints against User and Customer tables. Triggers 6-digit numeric OTP generation.
- POST /auth/token: Standard OAuth2 password flow. Validates credentials using Bcrypt (password hashes) and returns JWT access tokens.
- POST /auth/verify-otp: Validates OTPToken records by purpose (registration, reset, transaction).
- POST /auth/forgot-password: Generates a 15-minute expiration PasswordResetToken and sends a secure URL-safe link via Resend.
- GET /auth/verify-link: HTML-rendered magic link verification for seamless user onboarding.

2. User Profile and Settings (router: profile_router)

- GET /users/me: Returns FullUserResponse, joining Customer and Account tables for a unified view.
- PATCH /users/update-profile: Selective updates using ProfileUpdate pydantic model.
- PATCH /users/update-preferences: Manages UserSettings table (Theme, Language, Notification toggles).

3. Banking Operations (Main app & feature routers)

- POST /make_transaction: Integrated with SentinelAgent for real-time risk assessment. Returns approved/blocked status based on score thresholds.
- POST /transactions/internal-transfer: Executes cross-account movements within a single DB transaction.
- GET/PATCH /accounts & /cards: Full CRUD for managing banking instruments, including freezing status logic and daily limit management.
- GET /transactions/filter: Advanced querying by date ranges, amount thresholds, and transaction types.

4. Admin and Intelligence

- POST /webhooks/inbound-email: Protected by Svix signature verification. Parses payload to trigger background AI routing tasks.
- GET /admin/analytics: Provides transaction volume, fraud trends, and user growth aggregates.
- GET /audit/logs: Exposes AuditLogOut records tracking actor IDs, specific actions, and target entities.

SECURITY AND RELIABILITY ARCHITECTURE

- Database Concurrency: Critical transaction paths utilize 'with_for_update()' session locking to ensure strict data consistency and prevent race conditions during concurrent transfers.
- Payload Validation: Every endpoint is strictly typed with Pydantic schemas (UserCreate, TransactionRequest, etc.) to prevent malformed data injection.
- Signature Verification: All inbound webhooks (Resend/Svix) require header-based signature matching to prevent unauthorized external triggers.
- RBAC Logic: Admin endpoints enforce role checking (user.role == 'admin') at the route/dependency level.

NEXT TECHNICAL STEPS

- Kafka Integration: Transitioning to event-driven messaging for high-volume transaction processing.
- Celery + Redis: Moving BackgroundTasks to a dedicated distributed worker queue for heavier AI operations and scheduled audits.

Sentinel Bank technical foundation is solid and ready for production scaling.
