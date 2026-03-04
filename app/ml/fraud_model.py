# ML FRAUD SCORER

import joblib
import pandas as pd

from app.data.dataset_loader import DatasetLoader
from app.ml.feature_engineering import FraudFeatureBuilder


class MLScorer:
    """
    Loads trained fraud model and produces fraud probability.
    This model does NOT override policy.
    It acts as a secondary anomaly detection signal.
    """

    def __init__(self, dataset_loader):
        # Load trained model
        self.model = joblib.load("app/ml/model.pkl")

        # Load dataset (passed from SentinelAgent)
        self.dataset_loader = dataset_loader

        # Feature builder
        self.builder = FraudFeatureBuilder()

    def predict(self, transaction: dict) -> float:
        """
        Returns fraud probability between 0 and 1.
        """

        # Fetch transaction history for same account safely
        account_id = transaction.get("account_id")
        
        if account_id:
            history = self.dataset_loader.transactions[
                self.dataset_loader.transactions["account_id"] == account_id
            ]
        else:
            # If this is a live payload that only provides account_number, we can fall back to empty history
            # The builder will handle the empty dataframe.
            history = pd.DataFrame()

        # Build feature vector
        features = self.builder.build(transaction, history)

        # Predict probability of fraud class (1)
        probability = self.model.predict_proba(features)[0][1]

        return float(probability)