# Sentinel Bank - Database Setup

## Remote Database (Aiven PostgreSQL)

This project uses a **PostgreSQL** database hosted on [Aiven](https://aiven.io).

### Schema Overview

The database contains **5 tables**:

| Table          | Primary Key              | Description                                              |
| -------------- | ------------------------ | -------------------------------------------------------- |
| `customers`    | `customer_id` (UUID)     | Customer profiles — name, BVN, NIN, contact info, branch |
| `accounts`     | `account_id` (UUID)      | Bank accounts linked to customers                        |
| `transactions` | `transaction_id` (UUID)  | Transaction records with fraud scoring & merchant info   |
| `complaints`   | `complaint_id` (VARCHAR) | Customer complaints with SLA tracking & sentiment        |
| `users`        | `id` (SERIAL)            | App authentication — username, email, hashed password    |

### Relationships

```
customers (1) ──→ (N) accounts
customers (1) ──→ (N) complaints
accounts  (1) ──→ (N) transactions
transactions (1) ──→ (N) complaints
```

### Getting Started

1. **Get credentials** from the team lead or the Aiven Console.
2. **Copy** `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. **Fill in** your Aiven credentials in the `.env` file.

### Environment Variables

| Variable      | Description                 |
| ------------- | --------------------------- |
| `DB_HOST`     | Aiven service hostname      |
| `DB_PORT`     | Connection port             |
| `DB_NAME`     | Database name (`defaultdb`) |
| `DB_USER`     | Username (`avnadmin`)       |
| `DB_PASSWORD` | Aiven password              |
| `DB_SSL`      | SSL mode (`require`)        |

### Creating the Schema

Install dependencies and run the schema script:

```bash
pip install psycopg2-binary python-dotenv
python database/create_schema.py
```

### Testing Your Connection

You can test the connection using `psql`:

```bash
psql "postgresql://avnadmin:<password>@<host>:<port>/defaultdb?sslmode=require"
```
