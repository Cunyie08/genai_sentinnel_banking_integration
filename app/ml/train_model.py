# TRAIN FRAUD ML MODEL (Efficient + Behavioral-Aware)

# Import all necssary libraries and directory
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from app.ml.feature_engineering import FraudFeatureBuilder
from app.data.dataset_loader import DatasetLoader
from app.data.repository import BankRepository

# Load transactions.csv into memory
repo = BankRepository()
dataset_loader = DatasetLoader(repo)

# Extract transactions from dataframe
transactions = repo.dataset_loader.transactions

# Convert timestamp column to datetime for proper sorting
transactions["transaction_timestamp"] = pd.to_datetime(
    transactions["transaction_timestamp"]
)

# X_list = []
# y_list = []

# builder = FraudFeatureBuilder()

# Sort cumulative features by chronological calculations
transactions = transactions.sort_values(
    ["account_id", "transaction_timestamp"]
)

# Use cumcount() for the no of prior transactions per account
transactions["txn_count_so_far"] = (transactions.groupby("account_id").cumcount())

"""
Why this works:
- First transaction → 0
- Second transaction → 1
- Third → 2 etc.
This gives ML awareness of customer transaction history progression without heavy filtering or time-window computation

"""

# Create empty feature DataFrame
X = pd.DataFrame()

# Transaction amount (core numeric signal)
X["amount"] = transactions["amount"]

# Channel indicators (categorical → numeric flags)
X["is_atm"] = (transactions["channel"] == "atm").astype(int)
X["is_pos"] = (transactions["channel"] == "pos").astype(int)
X["is_mobile"] = (transactions["channel"] == "mobile_app").astype(int)

# Failure status signal
X["is_failed"] = (
    transactions["transaction_status"] == "failed"
).astype(int)

# Merchant risk proxy (fintech category higher fraud risk)
X["is_fintech"] = (
    transactions["merchant_category"] == "fintech"
).astype(int)

# Behavioral feature
X["txn_count_so_far"] = transactions["txn_count_so_far"]


# Define Target Variable
y = transactions["is_fraud_score"]  # Supervised learning target


# Train Model

"""
RandomForest was selected because, it:
- Handles non-linearity
- Works well with tabular data
- No scaling required
- Stable for synthetic dataset
 
"""

model = RandomForestClassifier(
    n_estimators=100,      # Number of trees
    max_depth=8,           # Prevent overfitting
    random_state=42        # Reproducibility
)

# Fit model
model.fit(X, y)


# Save trained model for inference inside SentinelAgent
joblib.dump(model, "app/ml/model.pkl")

print("Model trained and saved.")