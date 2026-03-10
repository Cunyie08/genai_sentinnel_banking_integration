"""
populate_customer_credentials.py
=================================
Reads the `customers_with_login.csv` file and backfills the `username`
and `password` columns for each matching customer in the database based on name matching.
"""

import asyncio
import csv
import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load from app/.env since we run this from the root directory
load_dotenv("app/.env")

from sqlalchemy import text
from app.data.db_connections import get_engine

async def populate():
    csv_file = Path(__file__).parent / "customers_with_login.csv"
    
    if not csv_file.exists():
        print(f"Error: Could not find {csv_file}")
        return

    engine = get_engine()
    
    print("Reading CSV and mapping credentials based on First/Last Name...")
    csv_creds_by_name = {}
    
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k}
            fname = cleaned.get("first_name", "").lower()
            lname = cleaned.get("last_name", "").lower()
            un = cleaned.get("username")
            pw = cleaned.get("password")
            
            if fname and lname and un and pw:
                # Key by name tuple
                csv_creds_by_name[(fname, lname)] = {"uname": un, "pwd": pw}
                
    if not csv_creds_by_name:
        print("No valid name-based credentials extracted from CSV")
        return
        
    print(f"Loaded {len(csv_creds_by_name)} name-credential mappings. Querying DB...")
    
    updates_to_make = []
    async with engine.begin() as conn:
        r = await conn.execute(text("SELECT customer_id, first_name, last_name FROM customers"))
        for row in r.fetchall():
            c_id = row[0]
            db_fname = row[1].strip().lower()
            db_lname = row[2].strip().lower()
            
            match = csv_creds_by_name.get((db_fname, db_lname))
            if match:
                updates_to_make.append({
                    "c_id": c_id,
                    "uname": match["uname"],
                    "pwd": match["pwd"]
                })
                
        if not updates_to_make:
            print("No names in the DB matched names in the CSV.")
            return
            
        print(f"Successfully matched {len(updates_to_make)} DB customers to CSV credentials! Committing updates in batches...")
        
        for batch_idx in range(0, len(updates_to_make), 500):
            batch = updates_to_make[batch_idx:batch_idx+500]
            stmt = text("UPDATE customers SET username = :uname, password = :pwd WHERE customer_id = :c_id")
            await conn.execute(stmt, batch)
            print(f"Executed batch ending at index {batch_idx + len(batch)}")

    await engine.dispose()
    print("[Migration] Credentials successfully backfilled to customers table.")

if __name__ == "__main__":
    asyncio.run(populate())
