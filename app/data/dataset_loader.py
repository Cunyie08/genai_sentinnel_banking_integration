from pathlib import Path
import pandas as pd


from sqlalchemy import select
from Backend.database import SessionLocal
from Backend.models import Customer, Account, Transaction, Complaint

class DatasetLoader:
    """
    Loads Sentinel Bank data organically from the remote PostgreSQL database.
    Because fetching from DB via SQLAlchemy is asynchronous, callers must invoke:
        loader = DatasetLoader()
        await loader.load()
    """

    def __init__(self):
        # Initialize empty dataframes to preserve API contract
        self.customers = pd.DataFrame()
        self.accounts = pd.DataFrame()
        self.transactions = pd.DataFrame()
        self.complaints = pd.DataFrame()

    async def load(self):
        """Asynchronously fetches all records and populates underlying Pandas DataFrames."""
        async with SessionLocal() as db:
            # 1. Fetch Customers
            cust_stmt = select(Customer)
            cust_res = await db.execute(cust_stmt)
            customers_list = [row.__dict__ for row in cust_res.scalars().all()]
            for item in customers_list:
                item.pop('_sa_instance_state', None)
            if customers_list:
                self.customers = pd.DataFrame(customers_list)
            else:
                self.customers = pd.DataFrame(columns=["customer_id", "first_name", "last_name", "age", "account_type", "current_balance"])

            # 2. Fetch Accounts
            acc_stmt = select(Account)
            acc_res = await db.execute(acc_stmt)
            accounts_list = [row.__dict__ for row in acc_res.scalars().all()]
            for item in accounts_list:
                item.pop('_sa_instance_state', None)
            if accounts_list:
                self.accounts = pd.DataFrame(accounts_list)
            else:
                self.accounts = pd.DataFrame(columns=["account_id", "customer_id", "account_number"])

            # 3. Fetch Transactions
            txn_stmt = select(Transaction)
            txn_res = await db.execute(txn_stmt)
            transactions_list = [row.__dict__ for row in txn_res.scalars().all()]
            for item in transactions_list:
                item.pop('_sa_instance_state', None)
            if transactions_list:
                self.transactions = pd.DataFrame(transactions_list)
            else:
                self.transactions = pd.DataFrame(columns=["transaction_id", "account_id", "transaction_type", "amount", "merchant_category", "merchant_name", "car_loan_signal_score"])

            # 4. Fetch Complaints
            comp_stmt = select(Complaint)
            comp_res = await db.execute(comp_stmt)
            complaints_list = [row.__dict__ for row in comp_res.scalars().all()]
            for item in complaints_list:
                item.pop('_sa_instance_state', None)
            if complaints_list:
                self.complaints = pd.DataFrame(complaints_list)
            else:
                self.complaints = pd.DataFrame(columns=["complaint_id", "customer_id"])

        # Normalize timestamps for downstream processing exactly as originally expected
        if "transaction_timestamp" in self.transactions.columns:
            self.transactions["transaction_timestamp"] = pd.to_datetime(
                self.transactions["transaction_timestamp"], errors="coerce"
            )

        if "complaint_timestamp" in self.complaints.columns:
            self.complaints["complaint_timestamp"] = pd.to_datetime(
                self.complaints["complaint_timestamp"], errors="coerce"
            )