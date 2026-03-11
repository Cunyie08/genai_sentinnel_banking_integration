import asyncio
from dotenv import load_dotenv
load_dotenv('app/.env')

from sqlalchemy import text
from Backend.database import Base, engine

# Import all models to ensure they are registered with Base.metadata
import Backend.models

async def create_all():
    async with engine.begin() as conn:
        print("Creating all tables from Backend.models...")
        await conn.run_sync(Base.metadata.create_all)
        print("Done creating tables.")
        
if __name__ == "__main__":
    asyncio.run(create_all())
