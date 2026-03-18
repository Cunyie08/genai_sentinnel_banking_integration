import asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from app.data.db_connections import get_engine

# 🔑 Ensure PostgreSQL env is loaded
load_dotenv()

async def check():
    engine = get_engine()

    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE LENGTH(fraud_explainability_trace) > 50) AS long_text_rows,
                COUNT(*) FILTER (WHERE LENGTH(fraud_explainability_trace) <= 50) AS short_flag_rows,
                COUNT(*) AS total
            FROM public.transactions
        """))

        row = result.fetchone()

        print("\n📊 Fraud Explainability Trace Analysis:\n")
        print(f"Long text rows  : {row[0]:,}")
        print(f"Short flag rows : {row[1]:,}")
        print(f"Total           : {row[2]:,}")

asyncio.run(check())