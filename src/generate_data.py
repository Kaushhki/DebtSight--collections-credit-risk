"""
generate_data.py
-----------------
Generates a realistic (intentionally messy) synthetic dataset for a
Collections & Credit Risk portfolio: customers, loans, and repayment
transactions. The data includes duplicates, nulls, type inconsistencies,
and out-of-range values on purpose, so the cleaning/validation pipeline
in data_cleaning.py has real work to do.

Run:
    python src/generate_data.py
Outputs:
    data/customers_raw.csv
    data/loans_raw.csv
    data/repayments_raw.csv
"""

import random
import string
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

N_CUSTOMERS = 1200
N_LOANS = 2000
SEGMENTS = ["Retail", "SME", "Corporate", "Agri", "Microfinance"]
STATES = ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Gujarat",
          "West Bengal", "Uttar Pradesh", "Telangana"]
LOAN_TYPES = ["Personal", "Auto", "Home", "Business", "Education"]
TODAY = datetime(2026, 7, 1)


def _rand_date(start_days_ago, end_days_ago):
    days = random.randint(end_days_ago, start_days_ago)
    return TODAY - timedelta(days=days)


def gen_customers(n):
    rows = []
    for i in range(1, n + 1):
        cust_id = f"CUST{i:05d}"
        segment = random.choice(SEGMENTS)
        state = random.choice(STATES)
        credit_score = int(np.clip(np.random.normal(680, 90), 300, 900))
        # Inject occasional dirty data
        if random.random() < 0.02:
            credit_score = None
        rows.append({
            "customer_id": cust_id,
            "segment": segment,
            "state": state,
            "credit_score": credit_score,
            "onboarding_date": _rand_date(1500, 60).strftime("%Y-%m-%d"),
        })
    df = pd.DataFrame(rows)
    # Inject a handful of duplicate customer rows (common real-world issue)
    dupes = df.sample(15, random_state=1)
    df = pd.concat([df, dupes], ignore_index=True)
    return df


def gen_loans(n, customer_ids):
    rows = []
    for i in range(1, n + 1):
        loan_id = f"LN{i:06d}"
        cust_id = random.choice(customer_ids)
        principal = round(random.choice([
            np.random.uniform(20000, 150000),      # Personal-ish
            np.random.uniform(150000, 1200000),     # Auto/Home-ish
            np.random.uniform(5000, 50000),         # Micro
        ]), 2)
        disb_date = _rand_date(900, 30)
        tenor_months = random.choice([6, 12, 18, 24, 36, 48, 60])
        interest_rate = round(np.random.uniform(8.5, 22.0), 2)
        loan_type = random.choice(LOAN_TYPES)

        # Overdue simulation: days past due (0 = current)
        dpd_roll = random.random()
        if dpd_roll < 0.55:
            dpd = 0
        elif dpd_roll < 0.75:
            dpd = random.randint(1, 30)
        elif dpd_roll < 0.88:
            dpd = random.randint(31, 60)
        elif dpd_roll < 0.96:
            dpd = random.randint(61, 90)
        else:
            dpd = random.randint(91, 240)

        status = "Closed" if random.random() < 0.1 else (
            "Written Off" if dpd > 180 else "Active"
        )

        # Inject dirty data
        if random.random() < 0.015:
            principal = None
        if random.random() < 0.01:
            interest_rate = -abs(interest_rate)  # invalid negative rate
        if random.random() < 0.01:
            tenor_months = None

        rows.append({
            "loan_id": loan_id,
            "customer_id": cust_id,
            "loan_type": loan_type,
            "principal_amount": principal,
            "interest_rate": interest_rate,
            "tenor_months": tenor_months,
            "disbursement_date": disb_date.strftime("%Y-%m-%d"),
            "days_past_due": dpd,
            "loan_status": status,
        })
    df = pd.DataFrame(rows)
    # A few duplicate loan_ids with conflicting data (data entry error)
    dupe_idx = df.sample(8, random_state=2).index
    dupes = df.loc[dupe_idx].copy()
    dupes["days_past_due"] = dupes["days_past_due"] + random.randint(1, 5)
    df = pd.concat([df, dupes], ignore_index=True)
    # A couple of orphan loans referencing a non-existent customer
    orphan_rows = df.sample(3, random_state=3).copy()
    orphan_rows["customer_id"] = "CUST99999"
    orphan_rows["loan_id"] = [f"LN99{i}" for i in range(3)]
    df = pd.concat([df, orphan_rows], ignore_index=True)
    return df


def gen_repayments(loans_df):
    rows = []
    txn_counter = 1
    for _, loan in loans_df.iterrows():
        if pd.isna(loan["principal_amount"]) or pd.isna(loan["tenor_months"]):
            continue
        n_payments = random.randint(1, 12)
        emi = round(loan["principal_amount"] / max(loan["tenor_months"], 1), 2)
        for _ in range(n_payments):
            pay_date = _rand_date(700, 1)
            amount = round(emi * np.random.uniform(0.7, 1.05), 2)
            method = random.choice(["NACH", "UPI", "Cheque", "Cash", "NEFT"])
            # Inject dirty data
            if random.random() < 0.005:
                amount = -abs(amount)  # invalid negative payment
            if random.random() < 0.01:
                amount = None
            rows.append({
                "transaction_id": f"TXN{txn_counter:07d}",
                "loan_id": loan["loan_id"],
                "payment_date": pay_date.strftime("%Y-%m-%d"),
                "amount_paid": amount,
                "payment_method": method,
            })
            txn_counter += 1
    df = pd.DataFrame(rows)
    # Duplicate a few transactions (common ingestion bug: double-posted payments)
    dupes = df.sample(20, random_state=4)
    df = pd.concat([df, dupes], ignore_index=True)
    return df


def main():
    customers = gen_customers(N_CUSTOMERS)
    loans = gen_loans(N_LOANS, customers["customer_id"].unique().tolist())
    repayments = gen_repayments(loans)

    customers.to_csv("data/customers_raw.csv", index=False)
    loans.to_csv("data/loans_raw.csv", index=False)
    repayments.to_csv("data/repayments_raw.csv", index=False)

    print(f"customers_raw.csv  -> {len(customers)} rows")
    print(f"loans_raw.csv      -> {len(loans)} rows")
    print(f"repayments_raw.csv -> {len(repayments)} rows")


if __name__ == "__main__":
    main()
