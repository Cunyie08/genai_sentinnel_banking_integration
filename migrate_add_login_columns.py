"""
One-shot migration: adds `username` and `password` columns to the
`customers` table if they don't already exist.

Run once from your project root:
    python migrate_add_login_columns.py

Safe to re-run - uses IF NOT EXISTS so it won't crash if already applied.
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import text
from app.data.db_connections import get_engine

# Explicitly load from app/.env since we run this from the root directory
# load_dotenv("app/.env")

def _load_env():
    for env_file in (".env", ".env.local"):
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key   = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value
            print(f"[Migration] Loaded env from {env_file}")
            return
    print("[Migration] No .env file found — relying on environment variables")

_load_env()


async def migrate():
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("[Migration] ERROR: DATABASE_URL is not set.")
        return

    print(f"[Migration] Connecting to: {db_url[:50]}...")
    engine = get_engine()

    async with engine.begin() as conn:

        # customers: login columns 
        await conn.execute(text("""
            ALTER TABLE customers
            ADD COLUMN IF NOT EXISTS username VARCHAR(100),
            ADD COLUMN IF NOT EXISTS password VARCHAR(100)
        """))
        print("[Migration] ✔  customers.username + password")

        # complaints: narration column 
        await conn.execute(text("""
            ALTER TABLE complaints
            ADD COLUMN IF NOT EXISTS complaint_narration TEXT
        """))
        print("[Migration] ✔  complaints.complaint_narration")

    await engine.dispose()
    print("[Migration] Done. Re-run your agent now.")


if __name__ == "__main__":
    asyncio.run(migrate())

# async def migrate():
#     engine = get_engine()
#     async with engine.begin() as conn:
#         # We split the ADD COLUMN commands because SQLite doesn't support adding 
#         # multiple columns in a single ALTER TABLE statement, and it's safer across dialects.
#         try:
#             await conn.execute(text("""
#                 ALTER TABLE customers
#                 ADD COLUMN IF NOT EXISTS username VARCHAR(100);
#             """))
#         except Exception as e:
#             print(f"Column 'username' might already exist or error occurred: {e}")
            
#         try:
#             await conn.execute(text("""
#                 ALTER TABLE customers
#                 ADD COLUMN IF NOT EXISTS password VARCHAR(100);
#             """))
#         except Exception as e:
#             print(f"Column 'password' might already exist or error occurred: {e}")
            
#         print("[Migration] username + password columns added to customers table")

#     await engine.dispose()
#     print("[Migration] Done. Re-run your agent now.")

# if __name__ == "__main__":
#     asyncio.run(migrate())
