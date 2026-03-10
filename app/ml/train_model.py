# TRAIN FRAUD ML MODEL (Efficient + Behavioral-Aware)

# Import all necssary libraries and directory
import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from app.ml.feature_engineering import FraudFeatureBuilder
from app.data.dataset_loader import DatasetLoader
from app.data.db_connections import get_engine, init_db
from app.data.repository import BankRepository

# Load transactions.csv into memory
_DATA_DIR = os.getenv(
    "SENTINEL_DATA_DIR",
    os.path.dirname(os.path.abspath(__file__))   # project root
)
_CSV_PATH = os.path.join(_DATA_DIR, "transactions.csv")

if not os.path.exists(_CSV_PATH):
    raise FileNotFoundError(
        f"transactions.csv not found at: {_CSV_PATH}\n"
        f"Set SENTINEL_DATA_DIR env var to the folder containing your CSVs."
    )

print(f"[Train] Loading transactions from: {_CSV_PATH}")
transactions = pd.read_csv(_CSV_PATH)
print(f"[Train] Loaded {len(transactions):,} rows")


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
).reset_index(drop=True)

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

print("[Train] Fitting model...")
model.fit(X, y)
print("[Train] Model trained.")

# Fit model
model.fit(X, y)


# Save trained model for inference inside SentinelAgent

output_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "app", "ml", "model.pkl"
)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
joblib.dump(model, output_path)
print(f"[Train] Model saved → {output_path}")
