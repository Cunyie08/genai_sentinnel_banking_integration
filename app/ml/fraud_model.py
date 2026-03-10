# ML FRAUD SCORER

import joblib
import pandas as pd

# from app.database.dataset_loader import DatasetLoader
from app.ml.feature_engineering import FraudFeatureBuilder


class MLScorer:
    """
    Loads trained fraud model and produces fraud probability.
    This model does NOT override policy.
    It acts as a secondary anomaly detection signal.
    """

    def __init__(self):
        # Load trained model
        self.model = joblib.load("app/ml/model.pkl")

        # Feature builder
        self.builder = FraudFeatureBuilder()

    def predict(self, transaction: dict, history_df: pd.DataFrame = None) -> float:
        """
        Returns fraud probability between 0 and 1.
        """
        if history_df is None:
            history_df = pd.DataFrame()

        # Build feature vector
        features = self.builder.build(transaction, history_df)

        # Predict probability of fraud class (1)
        probability = self.model.predict_proba(features)[0][1]

        return float(probability)