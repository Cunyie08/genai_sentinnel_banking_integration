import pandas as pd
from pathlib import Path

class DatasetLoader:
    """
    Loads Sentinnel Bank CSV datasets into memory.
    """

from pathlib import Path
import pandas as pd


class DatasetLoader:

    def __init__(self):

        # Project root
        # BASE_DIR = Path(__file__).resolve().parents[2]
        # data_path = BASE_DIR / "dataset"
        data_path = Path(r"C:\Users\USER\Documents\Final_Sentinel_Integrations\genai_sentinel_banking_integration\sentinnel_banking_dataset")

        

        self.customers = pd.read_csv(data_path / "customers.csv")
        self.accounts = pd.read_csv(data_path / "accounts.csv")
        self.transactions = pd.read_csv(data_path / "transactions.csv")
        self.complaints = pd.read_csv(data_path / "complaints.csv")

    # Normalize timestamps
        if "transaction_timestamp" in self.transactions.columns:
            self.transactions["transaction_timestamp"] = pd.to_datetime(
                self.transactions["transaction_timestamp"], errors="coerce"
            )

        if "complaint_timestamp" in self.complaints.columns:
            self.complaints["complaint_timestamp"] = pd.to_datetime(
                self.complaints["complaint_timestamp"], errors="coerce"
            )