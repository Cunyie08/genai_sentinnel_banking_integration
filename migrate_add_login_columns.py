"""
migrate_add_login_columns.py
=============================
One-shot migration: adds `username` and `password` columns to the
`customers` table if they don't already exist.

Run once from your project root:
    python migrate_add_login_columns.py

Safe to re-run - uses IF NOT EXISTS so it won't crash if already applied.
"""

import asyncio
from sqlalchemy import text
from app.data.db_connections import get_engine


async def migrate():
    engine = get_engine()

    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE customers
            ADD COLUMN IF NOT EXISTS username VARCHAR(100),
            ADD COLUMN IF NOT EXISTS password VARCHAR(100)
        """))
        print("[Migration] username + password columns added to customers table")

    await engine.dispose()
    print("[Migration] Done. Re-run your agent now.")


if __name__ == "__main__":
    asyncio.run(migrate())
