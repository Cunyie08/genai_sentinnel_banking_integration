import os
import ssl
from contextlib import asynccontextmanager
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Base for all ORM Models
base = declarative_base()

# S
def get_engine(echo: bool = False):
    """
    Priority:
        1. DATABASE_URL env var: PostgreSQL (production)
        2. Fallback: SQLite at app/data/sentinel_bank.db

    Args:
        echo:  If True, logs all SQL statements (dev debugging only).

    Returns:
        AsyncEngine
    """
    database_url = os.getenv("DATABASE_URL", "")

    if database_url:
        # Ensure 'postgresql://' prefix
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        # Ensure the async driver prefix is present
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        # asyncpg does NOT accept sslmode as a URL query param — TypeError crash.
        # Remove it entirely and handle SSL manually via connect_args below.
        parsed    = urlparse(database_url)
        params    = parse_qs(parsed.query)
        params.pop("sslmode", None)
        clean_qs  = urlencode({k: v[0] for k, v in params.items()})
        clean_url = urlunparse(parsed._replace(query=clean_qs))

        # Bild SSLContext explicitly for asyncpg
        # Supabase, Railway, and Neon use self-signed certs in their chain.
        # ssl=True uses Python's default verifier which rejects self-signed
        # certs with SSLCertVerificationError.
        # Passing an SSLContext with CERT_NONE encrypts the connection
        # without rejecting the self-signed certificate.
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode    = ssl.CERT_NONE

        engine = create_async_engine(
            clean_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"ssl": ssl_context},
        )
        print("[DB] Driver      -> asyncpg (PostgreSQL + SSL/no-verify)")

    else:
        # SQLite fallback (local dev)
        db_dir  = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "sentinel_bank.db")

        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )
        print(f"[DB] Driver      -> aiosqlite  (SQLite @ {db_path})")

    return engine

# Async session factory

def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Return a reusable async session factory bound to the given engine.

    The Orchestrator creates this once at startup and passes it to the
    Repository, no repeated engine lookups per request.

    Returns:
        async_sessionmaker[AsyncSession]
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,   # safe for async to avoid lazy-load errors
        autocommit=False,
        autoflush=False,
    )


@asynccontextmanager
async def get_async_session(engine: AsyncEngine):
    """
    Async context manager that yields a single AsyncSession.

    Automatically commits on success, rolls back on exception,
    and always closes each session.
    """
    factory = get_session_factory(engine)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise



# Initialize the schema

async def init_db(engine: AsyncEngine) -> None:
    """
    Create all tables defined in models.py if they don't exist.
    Safe to call on every startup — does nothing if tables already exist.
    """
    async with engine.begin() as connection:
        await connection.run_sync(base.metadata.create_all)
    print("[DB] Schema -> tables created / verified")


async def drop_db(engine: AsyncEngine) -> None:
    """
    Drop all tables. DESTRUCTIVE - dev only.

    Usage:
        await drop_db(engine)
    """
    async with engine.begin() as connection:
        await connection.run_sync(base.metadata.drop_all)
    print("[DB] Schema -> all tables dropped")


# Connection check

async def ping(engine: AsyncEngine) -> bool:
    """
    Lightweight connectivity check — runs SELECT 1.

    Returns:
        True if the database responds, False otherwise.
    """
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[DB] Ping failed -> {e}")
        return False




