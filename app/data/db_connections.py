import os
from contextlib import asynccontextmanager
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

        engine = create_async_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,   # silently drops old connections
            pool_size=10,
            max_overflow=20,
        )
        print("[DB] Driver -> asyncpg (PostgreSQL)")

    else:

        db_dir  = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "sentinel_bank.db")

        engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=echo,
            connect_args={"check_same_thread": False},
        )
        print(f"[DB] Driver -> aiosqlite (SQLite @ {db_path})")

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
    async with engine.begin() as connection:
        await connection.run_sync(base.metadata.create_all)
    print("[DB] Schema -> tables created / verified")


async def drop_db(engine: AsyncEngine) -> None:
    """
    Drop all tables. DESTRUCTIVE — dev only.

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




