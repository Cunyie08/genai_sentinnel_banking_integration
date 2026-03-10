# ML FRAUD SCORER

import joblib
import pandas as pd
import os
from app.data.dataset_loader import DatasetLoader
from app.ml.feature_engineering import FraudFeatureBuilder


# Feature column order must exactly match what train_model.py used
_FEATURE_COLUMNS = [
    "amount",
    "is_atm",
    "is_pos",
    "is_mobile",
    "is_failed",
    "is_fintech",
    "txn_count_so_far",
]

_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "model.pkl"
)

class MLScorer:
    """
    Loads the trained fraud model and returns a fraud probability (0–1).

    No DatasetLoader, no repository, no async — fully stateless.

    txn_count_so_far is read directly from the transaction dict because
    the seeder pre-computes it per account and stores it in the DB.
    If absent (live payload), defaults to 0 safely.
    """

    def __init__(self) -> None:
        # Load trained model
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"Trained model not found at: {_MODEL_PATH}\n"
                f"Run train_model.py first to generate model.pkl"
            )
        self.model = joblib.load(_MODEL_PATH)
    
    def predict(self, transaction: dict) -> float:
        """
        Build feature vector from transaction dict and return fraud probability.

        Args:
            transaction: Plain dict from SentinelRepository.get_transaction()

        Returns:
            float between 0.0 and 1.0
        """
        channel  = transaction.get("channel", "")
        category = transaction.get("merchant_category", "")
        status   = transaction.get("transaction_status", "")

        features = pd.DataFrame([{
            "amount":           float(transaction.get("amount") or 0),
            "is_atm":           int(channel  == "atm"),
            "is_pos":           int(channel  == "pos"),
            "is_mobile":        int(channel  == "mobile_app"),
            "is_failed":        int(status   == "failed"),
            "is_fintech":       int(category == "fintech"),
            # Pre-computed by seeder and stored on the transaction row.
            # Falls back to 0 for live/test payloads that omit it.
            "txn_count_so_far": int(transaction.get("txn_count_so_far") or 0),
        }])[_FEATURE_COLUMNS]   # enforce column order

        probability = self.model.predict_proba(features)[0][1]
        return float(probability)


    # def predict(self, transaction: dict) -> float:
    #     """
    #     Returns fraud probability between 0 and 1.
    #     """

    #     # Fetch transaction history for same account safely
    #     account_id = transaction.get("account_id")
        
    #     if account_id:
    #         history = self.dataset_loader.transactions[
    #             self.dataset_loader.transactions["account_id"] == account_id
    #         ]
    #     else:
    #         # If this is a live payload that only provides account_number, we can fall back to empty history
    #         # The builder will handle the empty dataframe.
    #         history = pd.DataFrame()

    #     # Build feature vector
    #     features = self.builder.build(transaction, history)

    #     # Predict probability of fraud class (1)
    #     probability = self.model.predict_proba(features)[0][1]

    #     return float(probability)