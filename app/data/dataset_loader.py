# Import libraries
import pandas as pd
from pathlib import Path
import os
import time
import asyncio
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine
from app.data.db_connections import get_engine, init_db
from Backend.models import Customer, Account, Transaction, Complaint


# CSV resolution

def _resolve_data_dir() -> str:
    """
    Find the directory containing the four generated CSVs.
    Checks GENAI_SENTINEL_BANKING_INTEGRATION env var -> app/data/csvs/ -> project root.
    """
    Candidates = [
        os.getenv("GENAI_SENTINEL_BANKING_INTEGRATION", ""),
        os.path.join(os.path.dirname(__file__), "csvs"),
        os.path.join(os.path.dirname(__file__), "..", "..", ""),
    ]
    for path in Candidates:
        if path and os.path.isfile(os.path.join(path, "customers.csv")):
            return os.path.abspath(path)

    raise FileNotFoundError(
        "Could not find customers.csv. "
        "Set GENAI_SENTINEL_BANKING_INTEGRATION env var or place CSVs in app/data/csvs/"
    )


CSV_FILES = {
    "customers":    "customers.csv",
    "accounts":     "accounts.csv",
    "transactions": "transactions.csv",
    "complaints":   "complaints.csv",
}



# DatasetLoader

class DatasetLoader:
    """
    Loads CSVs into the database at startup.

    All heavy CSV work (pandas, bulk insert) runs inside
    connection.run_sync() so the event loop is never blocked for
    the full duration of a large insert.
    """

    def __init__(self, engine: AsyncEngine):
        self.engine   = engine or get_engine()
        self.data_dir = _resolve_data_dir()
        print(f"[Seeder] Data dir: {self.data_dir}")


    # Public entry point
   
    async def seed(self, force: bool = False) -> None:
        """
        Seed all four tables from CSV files.

        Args:
            force:  If True, drops and recreates all tables first.
                    DESTRUCTIVE - use only in dev.
        """
        print("[Seeder] Sentinel Bank - Async Database Seeder")


        if force:
            from app.data.db_connections import drop_db
            print("[Seeder] Force mode - dropping all tables")
            await drop_db(self.engine)

        await init_db(self.engine)

        total_start = time.time()

        # Seed in FK-safe order
        await self._seed_customers()
        await self._seed_accounts()
        await self._seed_transactions()
        await self._seed_complaints()


        elapsed = time.time() - total_start
        print(f"\n[Seeder] All tables seeded in {elapsed:.1f}s")



    # Per-table seeders

    async def _seed_customers(self) -> None:
        await self._seed_table(
            csv_name  = CSV_FILES["customers"],
            table_name= Customer.__tablename__,
            transform = self._transform_customers,
        )

    async def _seed_accounts(self) -> None:
        await self._seed_table(
            csv_name  = CSV_FILES["accounts"],
            table_name= Account.__tablename__,
            transform = self._transform_accounts,
        )

    async def _seed_transactions(self) -> None:
        await self._seed_table(
            csv_name  = CSV_FILES["transactions"],
            table_name= Transaction.__tablename__,
            transform = self._transform_transactions,
            chunk_size= 5000,
        )

    async def _seed_complaints(self) -> None:
        await self._seed_table(
            csv_name  = CSV_FILES["complaints"],
            table_name= Complaint.__tablename__,
            transform = self._transform_complaints,
        )


    # Core async seeder

    async def _seed_table(
        self,
        csv_name:   str,
        table_name: str,
        transform,
        chunk_size: int = 1000,
    ) -> None:
        """
        Generic async CSV; DB seeder.

        Strategy:
            1. Check row count- skip if table already has data.
            2. Load CSV with pandas and apply type transformations.
            3. Insert in chunks via connection.run_sync(df.to_sql(...)).
               run_sync offloads the blocking pandas/SQLAlchemy Core work
               to a thread without holding the event loop.
            4. Commit after each chunk.
        """
        # Already seeded
        async with self.engine.connect() as connection:
            result = await connection.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            count = result.scalar()

        if count and count > 0:
            print(f"[Seeder]   {table_name:<16} already has {count:>8,} rows - skipped")
            return

        # Load &  transform CSV
        csv_path = os.path.join(self.data_dir, csv_name)
        if not os.path.isfile(csv_path):
            print(f"[Seeder]    {csv_name} not found - skipping {table_name}")
            return

        df    = pd.read_csv(csv_path, low_memory=False, encoding="utf-8")
        df    = transform(df)
        total = len(df)
        start = time.time()

        # Insert in chunks via run_sync
        inserted = 0
        for chunk_start in range(0, total, chunk_size):
            chunk = df.iloc[chunk_start : chunk_start + chunk_size]

            async with self.engine.begin() as conn:
                # run_sync runs the blocking pandas .to_sql() in a thread pool
                # so the event loop stays free during the insert
                await conn.run_sync(
                    lambda sync_conn, c=chunk: c.to_sql(
                        table_name,
                        con=sync_conn,
                        if_exists="append",
                        index=False,
                        method="multi",
                    )
                )
            inserted += len(chunk)

        elapsed = time.time() - start
        print(f"[Seeder]   {table_name:<16}  {inserted:>8,} rows  ({elapsed:.1f}s)")

    # Transformations
 
    @staticmethod
    def _transform_customers(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["date_of_birth"]   = pd.to_datetime(df["date_of_birth"],   errors="coerce").dt.date
        df["onboarding_date"] = pd.to_datetime(df["onboarding_date"], errors="coerce").dt.date
        df["solo_candidate"]  = df["solo_candidate"].astype(bool)
        if "username" not in df.columns: df["username"] = None
        if "password" not in df.columns: df["password"] = None
        return df

    @staticmethod
    def _transform_accounts(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["opened_date"]     = pd.to_datetime(df["opened_date"], errors="coerce").dt.date
        df["current_balance"] = pd.to_numeric(df["current_balance"], errors="coerce").fillna(0.0)
        return df

    @staticmethod
    def _transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["transaction_timestamp"] = pd.to_datetime(df["transaction_timestamp"], errors="coerce")
        df["amount"]                = pd.to_numeric(df["amount"],               errors="coerce").fillna(0.0)
        df["transaction_balance"]   = pd.to_numeric(df["transaction_balance"],   errors="coerce").fillna(0.0)
        df["Loan_signal_score"]     = pd.to_numeric(df["Loan_signal_score"],     errors="coerce").fillna(0.0)
        df["is_fraud_score"]        = pd.to_numeric(df["is_fraud_score"],        errors="coerce").fillna(0).astype(int)
        df["salary_detected"]       = df["salary_detected"].astype(bool)
        df["device_id"]             = df["device_id"].where(df["device_id"].notna(), None)
        return df

    @staticmethod
    def _transform_complaints(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["complaint_timestamp"]   = pd.to_datetime(df["complaint_timestamp"],  errors="coerce")
        df["resolution_timestamp"]  = pd.to_datetime(df["resolution_timestamp"], errors="coerce")
        df["sla_breach_flag"]       = pd.to_numeric(df["sla_breach_flag"],       errors="coerce").fillna(0).astype(int)
        df["fraud_related"]         = pd.to_numeric(df["fraud_related"],          errors="coerce").fillna(0).astype(int)
        df["resolution_time_hours"] = pd.to_numeric(df["resolution_time_hours"], errors="coerce").fillna(0).astype(int)
        return df



# CLI entry point

async def _main():
    import argparse
    parser = argparse.ArgumentParser(description="Sentinel Bank: Async Database Seeder")
    parser.add_argument(
        "--force", action="store_true",
        help="Drop and recreate all tables before seeding (dev only)"
    )
    args   = parser.parse_args()
    engine = get_engine()
    loader = DatasetLoader(engine)
    await loader.seed(force=args.force)


if __name__ == "__main__":
    asyncio.run(_main())


# class DatasetLoader:
#     """
#     Loads Sentinnel Bank CSV datasets into memory.
#     """

#     async def load_complaints(self):

#         """Load the complaints from the database"""
        
#         query = text("SELECT * FROM complaints")

#         async with AsyncSessionLocal() as seesion:
#               result = await session.execute(query)
#               rows = result.fetchall()

#         return rows
    
#     async def load_transactions(self):
         
#          """Load the customer's transaction from the database"""

#          query = text("SELECT * FROM transactions")

#          async with AsyncSessionLocal() as session:
#             result = await session.execute(query)
#             rows = result.fetchall()

#          return rows
    
#     async def load_accounts(self):
        
#         """Load the customer's account from the database"""
#         query = text("SELECT * FROM accounts")

#         async with AsyncSessionLocal() as session:
#             result = await session.execute(query)
#             rows = result.fetchall()

#         return rows
    

#     async def load_customers(self):

#         """Load the customer's details from the database"""

#         query = text("SELECT * FROM customers")

#         async with AsyncSessionLocal() as session:
#             result = await session.execute(query)
#             rows = result.fetchall()

#         return rows
            

              

    #     # Project root
    #     BASE_DIR = Path(__file__).resolve().parents[2]

    #     data_path = BASE_DIR

    #     self.customers = pd.read_csv(data_path / "customers.csv")
    #     self.accounts = pd.read_csv(data_path / "accounts.csv")
    #     self.transactions = pd.read_csv(data_path / "transactions.csv")
    #     self.complaints = pd.read_csv(data_path / "complaints.csv")

    # # Normalize timestamps
    #     if "transaction_timestamp" in self.transactions.columns:
    #         self.transactions["transaction_timestamp"] = pd.to_datetime(
    #             self.transactions["transaction_timestamp"], errors="coerce"
    #         )

    #     if "complaint_timestamp" in self.complaints.columns:
    #         self.complaints["complaint_timestamp"] = pd.to_datetime(
    #             self.complaints["complaint_timestamp"], errors="coerce"
    #         )

# class DatasetLoader:
#     """
#     Loads Sentinel Bank data organically from the remote PostgreSQL database.
#     Because fetching from DB via SQLAlchemy is asynchronous, callers must invoke:
#         loader = DatasetLoader()
#         await loader.load()
#     """

#     def __init__(self):
#         # Initialize empty dataframes to preserve API contract
#         self.customers = pd.DataFrame()
#         self.accounts = pd.DataFrame()
#         self.transactions = pd.DataFrame()
#         self.complaints = pd.DataFrame()

#     async def load(self):
#         """Asynchronously fetches all records and populates underlying Pandas DataFrames."""
#         async with SessionLocal() as db:
#             # 1. Fetch Customers
#             cust_stmt = select(Customer)
#             cust_res = await db.execute(cust_stmt)
#             customers_list = [row.__dict__ for row in cust_res.scalars().all()]
#             for item in customers_list:
#                 item.pop('_sa_instance_state', None)
#             if customers_list:
#                 self.customers = pd.DataFrame(customers_list)
#             else:
#                 self.customers = pd.DataFrame(columns=["customer_id", "first_name", "last_name", "age", "account_type", "current_balance"])

#             # 2. Fetch Accounts
#             acc_stmt = select(Account)
#             acc_res = await db.execute(acc_stmt)
#             accounts_list = [row.__dict__ for row in acc_res.scalars().all()]
#             for item in accounts_list:
#                 item.pop('_sa_instance_state', None)
#             if accounts_list:
#                 self.accounts = pd.DataFrame(accounts_list)
#             else:
#                 self.accounts = pd.DataFrame(columns=["account_id", "customer_id", "account_number"])

#             # 3. Fetch Transactions
#             txn_stmt = select(Transaction)
#             txn_res = await db.execute(txn_stmt)
#             transactions_list = [row.__dict__ for row in txn_res.scalars().all()]
#             for item in transactions_list:
#                 item.pop('_sa_instance_state', None)
#             if transactions_list:
#                 self.transactions = pd.DataFrame(transactions_list)
#             else:
#                 self.transactions = pd.DataFrame(columns=["transaction_id", "account_id", "transaction_type", "amount", "merchant_category", "merchant_name", "car_loan_signal_score"])

#             # 4. Fetch Complaints
#             comp_stmt = select(Complaint)
#             comp_res = await db.execute(comp_stmt)
#             complaints_list = [row.__dict__ for row in comp_res.scalars().all()]
#             for item in complaints_list:
#                 item.pop('_sa_instance_state', None)
#             if complaints_list:
#                 self.complaints = pd.DataFrame(complaints_list)
#             else:
#                 self.complaints = pd.DataFrame(columns=["complaint_id", "customer_id"])

#         # Normalize timestamps for downstream processing exactly as originally expected
#         if "transaction_timestamp" in self.transactions.columns:
#             self.transactions["transaction_timestamp"] = pd.to_datetime(
#                 self.transactions["transaction_timestamp"], errors="coerce"
#             )

#         if "complaint_timestamp" in self.complaints.columns:
#             self.complaints["complaint_timestamp"] = pd.to_datetime(
#                 self.complaints["complaint_timestamp"], errors="coerce"
#             )