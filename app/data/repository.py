# This file contains the database abstraction layer
from typing import Dict, Any
# from app.data.dataset_loader import DatasetLoader


class BankRepository:
    """
    Repository layer abstracting dataset access.
    Prevents agents from directly reading CSV files.
    """

    def __init__(self, dataset_loader):
        self.dataset_loader = dataset_loader

    # Dispatcher support
    def get_complaints(self, complaint_id: str): # returns a dictionary [str, Any] 

        complaint = self.dataset_loader.complaints[self.dataset_loader.complaints['complaint_id'] == complaint_id]

        if complaint.empty:
            raise ValueError(f"Complaint ID {complaint_id} not found")
        
        return complaint.iloc[0].to_dict()

    # Sentinel Support
    def get_transactions(self, transaction_id: str):

        txn = self.dataset_loader.transactions[self.dataset_loader.transactions['transaction_id']== transaction_id]
        
        if txn.empty:
            raise ValueError(f"Transaction ID {transaction_id} not found")

        return txn.iloc[0].to_dict()
    
    def get_customer_profile(self, customer_id: str):  
        # Ensure string comparison
        customer = self.dataset_loader.customers[
            self.dataset_loader.customers["customer_id"].astype(str) == str(customer_id)
        ]

        if customer.empty:
            raise ValueError(f"Customer ID {customer_id} not found.")

        return customer.iloc[0].to_dict()

    def get_customer_transactions(self, customer_id: str):
        if self.dataset_loader.accounts.empty or self.dataset_loader.transactions.empty:
            import pandas as pd
            return pd.DataFrame()
            
        customer_accounts = self.dataset_loader.accounts[
            self.dataset_loader.accounts["customer_id"].astype(str) == str(customer_id)
        ]["account_id"].tolist()

        return self.dataset_loader.transactions[
            self.dataset_loader.transactions["account_id"].isin(customer_accounts)
        ]