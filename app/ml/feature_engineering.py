import pandas as pd

# Must match train_model.py and fraud_model.py exactly
_FEATURE_COLUMNS = [
    "amount",
    "is_atm",
    "is_pos",
    "is_mobile",
    "is_failed",
    "is_fintech",
    "txn_count_so_far",
]

class FraudFeatureBuilder:

    @staticmethod
    def build(transaction: dict, history: pd.DataFrame):
        """
        Args:
            transaction: Plain dict from SentinelRepository.get_transaction()

        Returns:
            Single-row pd.DataFrame with columns matching _FEATURE_COLUMNS
        """

        # Basic transaction features
        channel  = transaction.get("channel", "")
        category = transaction.get("merchant_category", "")
        status   = transaction.get("transaction_status", "")

        
        features = {
            "amount":           float(transaction.get("amount") or 0),
            "is_atm":           int(channel  == "atm"),
            "is_pos":           int(channel  == "pos"),
            "is_mobile":        int(channel  == "mobile_app"),
            "is_failed":        int(status   == "failed"),
            "is_fintech":       int(category == "fintech"),
            "txn_count_so_far": int(transaction.get("txn_count_so_far") or 0),
        }

        # converts date to pandas datetime
        import datetime
        txn_time_str = transaction.get("transaction_timestamp", str(datetime.datetime.now()))
        txn_time = pd.to_datetime(txn_time_str)

        # history length represents number 
        # of prior transactions
        features["txn_count_so_far"] = len(history)

        return pd.DataFrame([features])[_FEATURE_COLUMNS]

        