# Data Layer — Sentinel Banking

This directory contains the data access and abstraction layer for the Sentinel Banking system.

It is responsible for:

Loading synthetic datasets

Providing structured access to customer, transaction, and complaint data

Isolating agents from raw data implementation details

This layer does not contain business logic.

## Components

### dataset_loader.py

The DatasetLoader class is responsible for loading structured CSV datasets into memory as pandas DataFrames.

### Loaded Datasets

customers_df
accounts_df
transactions_df
complaints_df

These datasets are generated synthetically and simulate realistic banking workflows.

The loader:

- Centralizes dataset loading

- Ensures consistent access paths

- Keeps file I/O separate from business logic

### repository.py

The BankRepository class provides structured query methods over the loaded datasets.

It acts as an abstraction layer between:

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