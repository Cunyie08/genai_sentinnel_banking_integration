# # TRAIN FRAUD ML MODEL (Efficient + Behavioral-Aware)

# # Import all necssary libraries and directory
# import os
# import pandas as pd
# import joblib
# import botocore
# from sklearn.ensemble import RandomForestClassifier
# from app.ml.feature_engineering import FraudFeatureBuilder
# from app.data.dataset_loader import DatasetLoader
# from app.data.db_connections import get_engine, init_db
# from app.data.repository import BankRepository

# # Load specific AWS Environment Variables
# S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
# S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
# REGION = os.getenv("REGION")
# S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# if not all([S3_ACCESS_KEY, S3_SECRET_ACCESS_KEY, REGION, S3_BUCKET_NAME]):
#     raise ValueError("Missing required AWS S3 environment variables. Ensure S3_ACCESS_KEY, S3_SECRET_ACCESS_KEY, REGION, and S3_BUCKET_NAME are set.")

# s3_uri = f"s3://{S3_BUCKET_NAME}/transactions.csv"
# print(f"[Train] Loading transactions from S3: {s3_uri}")

# try:
#     transactions = pd.read_csv(
#         s3_uri,
#         storage_options={
#             "key": S3_ACCESS_KEY,
#             "secret": S3_SECRET_ACCESS_KEY,
#             "client_kwargs": {"region_name": REGION}
#         }
#     )
#     print(f"[Train] Loaded {len(transactions):,} rows from S3")
# except botocore.exceptions.EndpointConnectionError as e:
#     raise ConnectionError(f"Network timeout or error connecting to S3 region '{REGION}': {str(e)}")
# except botocore.exceptions.ClientError as e:
#     error_code = e.response.get('Error', {}).get('Code', '')
#     if error_code in ['404', 'NoSuchKey']:
#         raise FileNotFoundError(f"transactions.csv not found in bucket '{S3_BUCKET_NAME}'.")
#     elif error_code in ['403', 'AccessDenied']:
#         raise PermissionError(f"Access Denied to bucket '{S3_BUCKET_NAME}'. Check your credentials.")
#     else:
#         raise
# except FileNotFoundError:
#     raise FileNotFoundError(f"transactions.csv not found in bucket '{S3_BUCKET_NAME}'.")
# except Exception as e:
#     raise RuntimeError(f"An unexpected error occurred while reading from S3: {str(e)}")


# # Convert timestamp column to datetime for proper sorting
# transactions["transaction_timestamp"] = pd.to_datetime(
#     transactions["transaction_timestamp"]
# )

# # X_list = []
# # y_list = []

# # builder = FraudFeatureBuilder()

# # Sort cumulative features by chronological calculations
# transactions = transactions.sort_values(
#     ["account_id", "transaction_timestamp"]
# ).reset_index(drop=True)

# # Use cumcount() for the no of prior transactions per account
# transactions["txn_count_so_far"] = (transactions.groupby("account_id").cumcount())

# """
# Why this works:
# - First transaction → 0
# - Second transaction → 1
# - Third → 2 etc.
# This gives ML awareness of customer transaction history progression without heavy filtering or time-window computation

# """

# # Create empty feature DataFrame
# X = pd.DataFrame()

# # Transaction amount (core numeric signal)
# X["amount"] = transactions["amount"]

# # Channel indicators (categorical → numeric flags)
# X["is_atm"] = (transactions["channel"] == "atm").astype(int)
# X["is_pos"] = (transactions["channel"] == "pos").astype(int)
# X["is_mobile"] = (transactions["channel"] == "mobile_app").astype(int)

# # Failure status signal
# X["is_failed"] = (
#     transactions["transaction_status"] == "failed"
# ).astype(int)

# # Merchant risk proxy (fintech category higher fraud risk)
# X["is_fintech"] = (
#     transactions["merchant_category"] == "fintech"
# ).astype(int)

# # Behavioral feature
# X["txn_count_so_far"] = transactions["txn_count_so_far"]


# # Define Target Variable
# y = transactions["is_fraud_score"]  # Supervised learning target


# # Train Model

# """
# RandomForest was selected because, it:
# - Handles non-linearity
# - Works well with tabular data
# - No scaling required
# - Stable for synthetic dataset
 
# """

# model = RandomForestClassifier(
#     n_estimators=100,      # Number of trees
#     max_depth=8,           # Prevent overfitting
#     random_state=42        # Reproducibility
# )

# print("[Train] Fitting model...")
# model.fit(X, y)
# print("[Train] Model trained.")

# # Fit model
# model.fit(X, y)


# # Save trained model for inference inside SentinelAgent

# output_path = os.path.join(
#     os.path.dirname(os.path.abspath(__file__)), "app", "ml", "model.pkl"
# )
# os.makedirs(os.path.dirname(output_path), exist_ok=True)
# joblib.dump(model, output_path)
# print(f"[Train] Model saved → {output_path}")
