import pandas as pd

class FraudFeatureBuilder:

    @staticmethod
    def build(transaction: dict, history: pd.DataFrame):

        # Basic transaction features
        features = {}

        features["amount"] = transaction.get("amount", 0)
        features["is_atm"] = int(transaction.get("channel") == "atm")
        features["is_pos"] = int(transaction.get("channel") == "pos")
        features["is_mobile"] = int(transaction.get("channel") == "mobile_app")
        features["is_failed"] = int(transaction.get("transaction_status") == "failed")
        features["is_fintech"] = int(transaction.get("merchant_category") == "fintech")
        
         # converts date to pandas datetime
        import datetime
        txn_time_str = transaction.get("transaction_timestamp", str(datetime.datetime.now()))
        txn_time = pd.to_datetime(txn_time_str)

        # history length represents number of prior transactions
        features["txn_count_so_far"] = len(history)
          

        return pd.DataFrame([features])