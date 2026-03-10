# This file contains the database abstraction layer
from typing import Dict, Any
from app.data.dataset_loader import DatasetLoader
import asyncio
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from app.data.db_connections import get_engine, get_session_factory
from Backend.models import Customer, Account, Transaction, Complaint


# Repository

class BankRepository:
    """
    Async data access layer for all Sentinel Bank agents.

    One instance is created by the Orchestrator at startup and injected
    into each agent that needs data access. No agent instantiates this
    class directly.

    Args:
        engine:   AsyncEngine instance. If None, one is created via
                  get_engine() (uses DATABASE_URL or SQLite fallback).

    """

    def __init__(self, engine: AsyncEngine = None):
        self._engine          = engine or get_engine()
        self._session_factory = get_session_factory(self._engine)

    # Internal session helper 

    def _session(self) -> AsyncSession:
        """Return a fresh AsyncSession from the shared factory."""
        return self._session_factory()


    # DISPATCHER AGENT - Complaint lookup

    async def get_complaint(self, complaint_id: str) -> Optional[dict]:
        """
        Fetch a single complaint by complaint_id.

        Enriches the result with a lightweight transaction summary
        (merchant, amount, channel, fraud flag) so the Dispatcher has
        context for routing decisions without a second agent call.

        Used by: DispatcherAgent

        Args:
            complaint_id: Primary key, e.g. "CMP-000001"

        Returns:
            dict with all complaint fields + "linked_transaction" sub-dict,
            or None if complaint_id is not found.
        """
        async with self._session() as session:
            complaint = await session.get(Complaint, complaint_id)
            if complaint is None:
                return None
            result = complaint.to_dict()

        # Enrich with linked transaction context (separate session is fine-
        # complaint dict is already detached)
        if result.get("linked_transaction_id"):
            txn = await self.get_transaction(result["linked_transaction_id"])
            if txn:
                result["linked_transaction"] = {
                    "merchant_category":          txn["merchant_category"],
                    "merchant_name":              txn["merchant_name"],
                    "amount":                     txn["amount"],
                    "channel":                    txn["channel"],
                    "transaction_status":         txn["transaction_status"],
                    "is_fraud_score":             txn["is_fraud_score"],
                    "fraud_explainability_trace": txn["fraud_explainability_trace"],
                    "transaction_timestamp":      txn["transaction_timestamp"],
                }

        return result

    # SENTINEL AGENT — Single transaction lookup

    async def get_transaction(self, transaction_id: str) -> Optional[dict]:
        """
        Fetch a single transaction by transaction_id.

        Used by: SentinelAgent (primary)
                 get_complaint() (enrichment)

        Args:
            transaction_id: UUID primary key

        Returns:
            dict with all transaction fields, or None if not found.
        """
        async with self._session() as session:
            txn = await session.get(Transaction, transaction_id)
            return txn.to_dict() if txn else None


    # TRAJECTORY AGENT — Full customer behavioral profile

    async def get_customer_profile(self, customer_id: str) -> Optional[dict]:
        """
        Build the full behavioral profile for a customer by aggregating
        their transaction history into the signals the Trajectory Agent
        needs for both VALIDATION and PROACTIVE recommendation modes.

        Signals computed:
            Loan_signal_score   - latest value from most recent transaction
            monthly_inflow      - total credit amount across all transactions
            monthly_outflow     - total debit amount across all transactions
            salary_detected     - True if any salary credit is flagged
            uber_tracker        - count of Uber / Bolt / LagRide transactions
            recommended_product - product assigned by data_generator
            account_type        - type of primary (highest-balance) account
            current_balance     - balance of primary account
            transaction_count   - total number of transactions
            recent_transactions - last 10 transactions (for agent context)

        Used by: TrajectoryAgent (both VALIDATION and PROACTIVE modes)

        Args:
            customer_id: UUID primary key

        Returns:
            dict with customer fields + aggregated behavioral signals,
            or None if customer_id is not found.
        """
        async with self._session() as session:

            # Customer base record 
            customer = await session.get(Customer, customer_id)
            if customer is None:
                return None
            profile = customer.to_dict()

            # All transactions for this customer 
            txn_stmt = (
                select(Transaction)
                .where(Transaction.customer_id == customer_id)
                .order_by(Transaction.transaction_timestamp.desc())
            )
            txn_result  = await session.execute(txn_stmt)
            transactions = txn_result.scalars().all()

            if not transactions:
                profile.update({
                    "Loan_signal_score":   0.0,
                    "monthly_inflow":      0.0,
                    "monthly_outflow":     0.0,
                    "salary_detected":     False,
                    "uber_tracker":        0,
                    "recommended_product": None,
                    "account_type":        "savings",
                    "current_balance":     0.0,
                    "transaction_count":   0,
                    "recent_transactions": [],
                })
                return profile

            # Behavioral signal aggregation 

            loan_signal_score = next((t.Loan_signal_score for t in transactions if t.Loan_signal_score is not None), 0.0)

            monthly_inflow  = sum(
                t.amount for t in transactions if t.transaction_type == "credit"
            )
            monthly_outflow = sum(
                t.amount for t in transactions if t.transaction_type == "debit"
            )

            salary_detected = any(t.salary_detected for t in transactions)

            RIDE_MERCHANTS = {"Uber", "Bolt", "LagRide"}
            uber_tracker   = sum(
                1 for t in transactions if t.merchant_name in RIDE_MERCHANTS
            )

            recommended_product = next((t.recommended_product for t in transactions if t.recommended_product is not None), None)

            # Snapshot to dict while session is still open
            recent_transactions = [t.to_dict() for t in transactions[:10]]

            # Primary account (highest balance) 
            acc_stmt = (
                select(Account)
                .where(Account.customer_id == customer_id)
                .order_by(Account.current_balance.desc())
            )
            acc_result      = await session.execute(acc_stmt)
            primary_account = acc_result.scalars().first()

            account_type    = primary_account.account_type    if primary_account else "savings"
            current_balance = primary_account.current_balance if primary_account else 0.0

        # Assemble profile (outside session — all data already captured) 
        profile.update({
            "Loan_signal_score":   loan_signal_score,
            "monthly_inflow":      round(monthly_inflow,  2),
            "monthly_outflow":     round(monthly_outflow, 2),
            "salary_detected":     salary_detected,
            "uber_tracker":        uber_tracker,
            "recommended_product": recommended_product,
            "account_type":        account_type,
            "current_balance":     current_balance,
            "transaction_count":   len(transactions),
            "recent_transactions": recent_transactions,
        })

        return profile


    # SHARED UTILITIES

    async def get_customer(self, customer_id: str) -> Optional[dict]:
        """
        Fetch a customer record by customer_id.

        Args:
            customer_id: UUID primary key

        Returns:
            dict with customer fields, or None if not found.
        """
        async with self._session() as session:
            customer = await session.get(Customer, customer_id)
            return customer.to_dict() if customer else None

    async def get_account(self, account_id: str) -> Optional[dict]:
        """
        Fetch a single account by account_id.

        Args:
            account_id: UUID primary key

        Returns:
            dict with account fields, or None if not found.
        """
        async with self._session() as session:
            account = await session.get(Account, account_id)
            return account.to_dict() if account else None

    async def get_customer_accounts(self, customer_id: str) -> list[dict]:
        """
        Fetch all accounts belonging to a customer.

        Args:
            customer_id: UUID primary key

        Returns:
            List of account dicts (empty list if none found).
        """
        async with self._session() as session:
            stmt     = select(Account).where(Account.customer_id == customer_id)
            result   = await session.execute(stmt)
            accounts = result.scalars().all()
            return [a.to_dict() for a in accounts]

    async def get_customer_complaints(self, customer_id: str) -> list[dict]:
        """
        Fetch all complaints for a customer, most recent first.

        Args:
            customer_id: UUID primary key

        Returns:
            List of complaint dicts ordered by complaint_timestamp desc.
        """
        async with self._session() as session:
            stmt = (
                select(Complaint)
                .where(Complaint.customer_id == customer_id)
                .order_by(Complaint.complaint_timestamp.desc())
            )
            result     = await session.execute(stmt)
            complaints = result.scalars().all()
            return [c.to_dict() for c in complaints]

    async def get_customer_transactions(self, customer_id: str) -> list[dict]:
        """
        Fetch all raw transactions for a customer, most recent first.

        This is the shared query used by both SentinelAgent (when looking
        up history for pattern analysis) and TrajectoryAgent (profile build).
        For the full aggregated profile use get_customer_profile() instead.

        Args:
            customer_id: UUID primary key

        Returns:
            List of transaction dicts ordered by transaction_timestamp desc.
        """
        async with self._session() as session:
            stmt = (
                select(Transaction)
                .where(Transaction.customer_id == customer_id)
                .order_by(Transaction.transaction_timestamp.desc())
            )
            result       = await session.execute(stmt)
            transactions = result.scalars().all()
            return [t.to_dict() for t in transactions]


    # HEALTH CHECK (Orchestrator + test suite)

    async def health_check(self) -> dict:
        """
        Return row counts for all four tables.
        Called by Orchestrator.initialize() to confirm DB is seeded.

        Returns:
            {
                "customers":    int,
                "accounts":     int,
                "transactions": int,
                "complaints":   int,
                "healthy":      bool,   # True if all tables have > 0 rows
            }
        """
        async with self._session() as session:
            counts = {
                "customers":    await session.scalar(
                    select(func.count()).select_from(Customer)
                ),
                "accounts":     await session.scalar(
                    select(func.count()).select_from(Account)
                ),
                "transactions": await session.scalar(
                    select(func.count()).select_from(Transaction)
                ),
                "complaints":   await session.scalar(
                    select(func.count()).select_from(Complaint)
                ),
            }

        counts["healthy"] = all(v and v > 0 for v in counts.values())
        return counts



# class BankRepository:
#     """
#     Repository layer abstracting dataset access.
#     Prevents agents from directly reading CSV files.
#     """

#     def __init__(self, dataset_loader):
#         self.dataset_loader = dataset_loader

#     # Dispatcher support
#     def get_complaints(self, complaint_id: str): # returns a dictionary [str, Any] 

#         complaint = self.dataset_loader.complaints[self.dataset_loader.complaints['complaint_id'] == complaint_id]

#         if complaint.empty:
#             raise ValueError(f"Complaint ID {complaint_id} not found")
        
#         return complaint.iloc[0].to_dict()

#     # Sentinel Support
#     def get_transactions(self, transaction_id: str):

#         txn = self.dataset_loader.transactions[self.dataset_loader.transactions['transaction_id']== transaction_id]
        
#         if txn.empty:
#             raise ValueError(f"Transaction ID {transaction_id} not found")

#         return txn.iloc[0].to_dict()
    
#     def get_customer_profile(self, customer_id: str):  
#         # Ensure string comparison
#         customer = self.dataset_loader.customers[
#             self.dataset_loader.customers["customer_id"].astype(str) == str(customer_id)
#         ]

#         if customer.empty:
#             raise ValueError(f"Customer ID {customer_id} not found.")

#         return customer.iloc[0].to_dict()

#     def get_customer_transactions(self, customer_id: str):
#         if self.dataset_loader.accounts.empty or self.dataset_loader.transactions.empty:
#             import pandas as pd
#             return pd.DataFrame()
            
#         customer_accounts = self.dataset_loader.accounts[
#             self.dataset_loader.accounts["customer_id"].astype(str) == str(customer_id)
#         ]["account_id"].tolist()

#         return self.dataset_loader.transactions[
#             self.dataset_loader.transactions["account_id"].isin(customer_accounts)
#         ]
