import asyncio
from dotenv import load_dotenv
import os

# Ensure the correct env is loaded
load_dotenv(os.path.join('app', '.env'))

from app.data.db_connections import get_engine
from Backend.models import Base

async def main():
    engine = get_engine()
    async with engine.begin() as conn:
        # Create all tables that are in Base.metadata but don't exist in DB
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables updated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
