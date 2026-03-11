import asyncio
from dotenv import load_dotenv
load_dotenv('app/.env')

from sqlalchemy import text
from app.data.db_connections import get_engine

async def drop_all():
    engine = get_engine()
    async with engine.begin() as conn:
        print("Dropping public schema cascade...")
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        print("Recreating public schema...")
        await conn.execute(text("CREATE SCHEMA public;"))
        
if __name__ == "__main__":
    asyncio.run(drop_all())
