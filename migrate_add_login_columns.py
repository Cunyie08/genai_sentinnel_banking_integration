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
import os
from dotenv import load_dotenv

# Explicitly load from app/.env since we run this from the root directory
load_dotenv("app/.env")

from sqlalchemy import text
from app.data.db_connections import get_engine

async def migrate():
    engine = get_engine()
    async with engine.begin() as conn:
        # We split the ADD COLUMN commands because SQLite doesn't support adding 
        # multiple columns in a single ALTER TABLE statement, and it's safer across dialects.
        try:
            await conn.execute(text("""
                ALTER TABLE customers
                ADD COLUMN IF NOT EXISTS username VARCHAR(100);
            """))
        except Exception as e:
            print(f"Column 'username' might already exist or error occurred: {e}")
            
        try:
            await conn.execute(text("""
                ALTER TABLE customers
                ADD COLUMN IF NOT EXISTS password VARCHAR(100);
            """))
        except Exception as e:
            print(f"Column 'password' might already exist or error occurred: {e}")
            
        print("[Migration] username + password columns added to customers table")

    await engine.dispose()
    print("[Migration] Done. Re-run your agent now.")

if __name__ == "__main__":
    asyncio.run(migrate())
