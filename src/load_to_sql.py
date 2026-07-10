"""
load_to_sql.py
---------------
Loads cleaned CSVs into a local SQLite database so the project can
demonstrate real SQL-based aggregation (see sql/*.sql) instead of only
pandas. SQLite is used for portability -- the queries in sql/ are
standard ANSI SQL and will run unmodified on Postgres/MySQL/SQL Server
with a real production loan book.

Run:
    python src/load_to_sql.py
Outputs:
    data/collections.db
"""

import sqlite3
import pandas as pd

DB_PATH = "data/collections.db"


def main():
    customers = pd.read_csv("data/customers_clean.csv")
    loans = pd.read_csv("data/loans_clean.csv")
    repayments = pd.read_csv("data/repayments_clean.csv")

    conn = sqlite3.connect(DB_PATH)
    customers.to_sql("customers", conn, if_exists="replace", index=False)
    loans.to_sql("loans", conn, if_exists="replace", index=False)
    repayments.to_sql("repayments", conn, if_exists="replace", index=False)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_loans_customer ON loans(customer_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_repay_loan ON repayments(loan_id)")
    conn.commit()
    conn.close()
    print(f"Loaded customers, loans, repayments into {DB_PATH}")


if __name__ == "__main__":
    main()
