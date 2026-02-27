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

        # Fetch transaction history for same account
        history = self.dataset_loader.transactions[
            self.dataset_loader.transactions["account_id"] ==
            transaction["account_id"]
        ]

        # Build feature vector
        features = self.builder.build(transaction, history)

        # Predict probability of fraud class (1)
        probability = self.model.predict_proba(features)[0][1]

        return float(probability)