import pandas as pd
from pathlib import Path

class DatasetLoader:
    """
    Loads Sentinnel Bank CSV datasets into memory.
    """

    # Read the dataset from the directory
    def __init__(self, base_path: str = "dataset"):
        self.customers = pd.read_csv(f"{base_path}/customers.csv")
        self.accounts = pd.read_csv(f"{base_path}/accounts.csv")
        self.transactions = pd.read_csv(f"{base_path}/transactions.csv")
        self.complaints = pd.read_csv(f"{base_path}/complaints.csv")

    # Normalize timestamps
        if "transaction_timestamp" in self.transactions.columns:
            self.transactions["transaction_timestamp"] = pd.to_datetime(
                self.transactions["transaction_timestamp"], errors="coerce"
            )

        if "complaint_timestamp" in self.complaints.columns:
            self.complaints["complaint_timestamp"] = pd.to_datetime(
                self.complaints["complaint_timestamp"], errors="coerce"
            )