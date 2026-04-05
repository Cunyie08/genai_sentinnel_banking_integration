# TRAIN FRAUD ML MODEL — Local CSV version
# Replaces the S3 version which requires AWS credentials.
# Reads transactions.csv from the same directory as the data generator.

import os
import sys
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

# ── Locate transactions.csv ────────────────────────────────────────────────
# Checks project root, then app/data/csvs/, same as DatasetLoader._resolve_data_dir()

def find_csv() -> str:
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "transactions.csv"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "data", "csvs", "transactions.csv"),
    ]
    # Also walk up to project root
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        candidate = os.path.join(here, "transactions.csv")
        if os.path.isfile(candidate):
            return candidate
        here = os.path.dirname(here)

    for c in candidates:
        if os.path.isfile(c):
            return c

    raise FileNotFoundError(
        "Could not find transactions.csv. "
        "Run data_generator.py first, or set the path manually in this script."
    )

csv_path = find_csv()
print(f"[Train] Loading transactions from: {csv_path}")

transactions = pd.read_csv(csv_path, low_memory=False)
print(f"[Train] Loaded {len(transactions):,} rows")

# ── Feature engineering ────────────────────────────────────────────────────

transactions["transaction_timestamp"] = pd.to_datetime(
    transactions["transaction_timestamp"], errors="coerce"
)

transactions = transactions.sort_values(
    ["account_id", "transaction_timestamp"]
).reset_index(drop=True)

transactions["txn_count_so_far"] = transactions.groupby("account_id").cumcount()

X = pd.DataFrame()
X["amount"]           = pd.to_numeric(transactions["amount"], errors="coerce").fillna(0)
X["is_atm"]           = (transactions["channel"] == "atm").astype(int)
X["is_pos"]           = (transactions["channel"] == "pos").astype(int)
X["is_mobile"]        = (transactions["channel"] == "mobile_app").astype(int)
X["is_failed"]        = (transactions["transaction_status"] == "failed").astype(int)
X["is_fintech"]       = (transactions["merchant_category"] == "fintech").astype(int)
X["txn_count_so_far"] = transactions["txn_count_so_far"]

y = pd.to_numeric(transactions["is_fraud_score"], errors="coerce").fillna(0).astype(int)

print(f"[Train] Features: {list(X.columns)}")
print(f"[Train] Fraud rate: {y.mean():.2%}  ({y.sum():,} fraud / {len(y):,} total)")

# ── Train ──────────────────────────────────────────────────────────────────

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=8,
    random_state=42,
    n_jobs=-1,          # use all CPU cores → faster training
)

print("[Train] Fitting model …")
model.fit(X, y)
print("[Train] Model trained.")

# ── Save to app/ml/model.pkl ───────────────────────────────────────────────

output_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "app", "ml", "model.pkl"
)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
joblib.dump(model, output_path)
print(f"[Train] Model saved → {output_path}")
print("[Train] Done. You can now start the backend.")