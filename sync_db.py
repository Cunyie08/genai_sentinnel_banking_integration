import asyncio
from sqlalchemy import text
from Backend.database import engine, Base
from Backend.models import Card, Notification, Account # Ensure models are imported for metadata

async def sync_db():
    print("Connecting to database...")
    async with engine.begin() as conn:
        # 1. Create new tables (Cards, Notifications)
        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        # 2. Add missing columns to existing tables
        print("Checking for missing columns...")
        alter_commands = [
            "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS account_status VARCHAR(20) DEFAULT 'active'",
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS card_number VARCHAR(20) UNIQUE",
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS expiry_date VARCHAR(10)",
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS cvv VARCHAR(4)",
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS daily_limit NUMERIC(18, 2) DEFAULT 100000.00",
            # Fix type mismatch in case they already exist with wrong type
            "ALTER TABLE cards ALTER COLUMN expiry_date TYPE VARCHAR(10) USING expiry_date::VARCHAR",
            "ALTER TABLE cards ALTER COLUMN cvv TYPE VARCHAR(4) USING cvv::VARCHAR",
            "ALTER TABLE notifications ALTER COLUMN notification_id TYPE VARCHAR(50) USING notification_id::VARCHAR",
            "ALTER TABLE notifications ALTER COLUMN user_id DROP NOT NULL",
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS notification_type VARCHAR(20) DEFAULT 'in-app'",
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS customer_id VARCHAR(50) REFERENCES customers(customer_id)",
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS title VARCHAR(100)",
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS message TEXT",
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE",
            "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ]
        
        for cmd in alter_commands:
            try:
                await conn.execute(text(cmd))
                print(f"Executed: {cmd}")
            except Exception as e:
                print(f"Error executing {cmd}: {e}")

    print("Success: Database schema is now in sync.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(sync_db())
