import pandas as pd

class FraudFeatureBuilder:

    @staticmethod
    def build(transaction: dict, history: pd.DataFrame):

        # Basic transaction features
        features = {}

        features["amount"] = transaction["amount"]
        features["is_atm"] = int(transaction["channel"] == "atm")
        features["is_pos"] = int(transaction["channel"] == "pos")
        features["is_mobile"] = int(transaction["channel"] == "mobile_app")
        features["is_failed"] = int(transaction["transaction_status"] == "failed")
        features["is_fintech"] = int(transaction["merchant_category"] == "fintech")
        
         # converts date to pandas datetime
        txn_time = pd.to_datetime(transaction['transaction_timestamp'])

        # history length represents number of prior transactions
        features["txn_count_so_far"] = len(history)
          

        return pd.DataFrame([features])