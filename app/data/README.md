# Data Layer - Sentinnel Banking

This directory contains the data access and abstraction layer for the Sentinnel Banking system.

It is responsible for:

- Loading synthetic datasets
- Providing structured access to customer, transaction, and complaint data
- Isolating agents from raw data implementation details
- This layer does not contain business logic.

## Components

### dataset_loader.py

The DatasetLoader class is responsible for loading structured CSV datasets into memory as pandas DataFrames.

#### Loaded Datasets
These datasets are generated synthetically and simulate realistic banking workflows.

- customers_df
- accounts_df
- transactions_df
- complaints_df


The loader:

- Centralizes dataset loading
- Ensures consistent access paths
- Keeps file I/O separate from business logic

### repository.py

The BankRepository class provides structured query methods over the loaded datasets. It acts as an abstraction layer between:

- Agents and
- Raw DataFrames

Available Methods

- get_customer_profile(customer_id)
- get_customer_transactions(customer_id)
- get_complaints(complaint_id)
- get_transactions(transaction_id)

These methods:

- Perform filtering
- Validate IDs
- Raise controlled errors if records are missing
- Return structured dictionaries or DataFrames
- Design Principles

The data layer follows:

- Separation of concerns
- Clear abstraction boundaries
- No business logic
- No policy enforcement

#### No ML computations

Agents are responsible for interpreting the data.
The repository is responsible only for retrieving it.

#### Why This Matters

This design ensures:
- Agents remain testable
- Data source can be swapped without changing agents
- Logic and storage remain decoupled
- System remains modular

### Data Source

All datasets are:

- Synthetic
- Generated via data_generator.py
- Designed to simulate realistic banking operations
- Free of real customer data

# Dataset Layer - Sentinel Banking Synthetic Data

This directory contains synthetic datasets used for:

- Fraud modeling
- Product recommendation
- Complaint routing
- Behavioral signal extraction

---

## Files

### data_generator.py

Generates synthetic banking data including:

- customers.csv
- accounts.csv
- transactions.csv
- complaints.csv

All datasets are internally consistent.

---

## Data Structure

### Customers
- customer_id
- age
- account_type
- Loan_signal_score

---

### Transactions
- transaction_id
- customer_id
- transaction_type
- amount
- merchant_category
- fraud_explainability_trace

---

### Complaints
- complaint_id
- customer_id
- complaint_text

---

## Behavioral Signals Derived

Trajectory Agent computes:

- monthly_inflow
- salary_detected
- uber_tracker
- DSR

Sentinel Agent computes:

- fraud flags
- merchant risk
- timing risk

---

## Important Notes

- Data is synthetic.
- No real customer data is used.
- Designed for testing policy-based AI systems.