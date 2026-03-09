"""
Sentinel Bank — Login Credential Generator
==========================================
Generates username + password for every customer in customers.csv.

Password formula:
    FirstName (capitalised) + DOB year + special symbol + last 3 digits of BVN
    e.g.  Zainab2001@334

Username formula:
    firstname.lastname + 4-digit zero-padded index  (all lowercase)
    e.g.  zainab.ekwugum0001

Outputs:
    - login_credentials.csv   (customer_id, username, password, email)
    - customers_with_login.csv (full customers.csv + username + password columns)
"""

import pandas as pd
import random

SYMBOLS = ["@", "#", "!", "$", "&", "*"]

def make_password(row):
    first    = str(row["first_name"]).capitalize()
    dob_year = str(pd.to_datetime(row["date_of_birth"]).year)
    symbol   = SYMBOLS[int(str(row["bvn"])[-1]) % len(SYMBOLS)]   # deterministic per customer
    bvn_tail = str(row["bvn"])[-3:]
    return f"{first}{dob_year}{symbol}{bvn_tail}"

def make_username(row, idx):
    first = str(row["first_name"]).lower().strip()
    last  = str(row["last_name"]).lower().strip()
    return f"{first}.{last}{str(idx).zfill(4)}"

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv("customers.csv")
print(f"Loaded {len(df):,} customers.")

# ── Generate ──────────────────────────────────────────────────────────────────
df["username"] = [make_username(row, i + 1) for i, (_, row) in enumerate(df.iterrows())]
df["password"] = df.apply(make_password, axis=1)

# ── login_credentials.csv ─────────────────────────────────────────────────────
creds_df = df[["customer_id", "full_name", "email", "username", "password"]].copy()
creds_df.to_csv("login_credentials.csv", index=False)
print(f"✔  login_credentials.csv  — {len(creds_df):,} rows")

# ── customers_with_login.csv ──────────────────────────────────────────────────
df.to_csv("customers_with_login.csv", index=False)
print(f"✔  customers_with_login.csv — {len(df):,} rows, {len(df.columns)} columns")

# ── Preview ───────────────────────────────────────────────────────────────────
print("\nSample credentials:")
print(creds_df[["full_name", "username", "password"]].head(8).to_string(index=False))
