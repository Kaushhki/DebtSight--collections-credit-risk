

import pandas as pd

ISSUES = []


def log_issue(table, rule, count, detail=""):
    ISSUES.append({"table": table, "rule": rule, "rows_affected": count, "detail": detail})
    print(f"[{table}] {rule}: {count} row(s) {detail}")


def clean_customers(df):
    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"], keep="first")
    log_issue("customers", "duplicate_customer_id_removed", before - len(df))

    missing_score = df["credit_score"].isna().sum()
    df["credit_score"] = df["credit_score"].fillna(df["credit_score"].median())
    log_issue("customers", "missing_credit_score_imputed_with_median", missing_score)

    out_of_range = ((df["credit_score"] < 300) | (df["credit_score"] > 900)).sum()
    df["credit_score"] = df["credit_score"].clip(300, 900)
    log_issue("customers", "credit_score_out_of_range_clipped", out_of_range)

    df["onboarding_date"] = pd.to_datetime(df["onboarding_date"], errors="coerce")
    bad_dates = df["onboarding_date"].isna().sum()
    log_issue("customers", "invalid_onboarding_date", bad_dates)

    return df.reset_index(drop=True)



def clean_loans(df, valid_customer_ids):
    before = len(df)
    df = df.drop_duplicates(subset=["loan_id"], keep="first")
    log_issue("loans", "duplicate_loan_id_removed", before - len(df))

    orphan_mask = ~df["customer_id"].isin(valid_customer_ids)
    orphan_count = orphan_mask.sum()
    df = df[~orphan_mask]
    log_issue("loans", "orphan_loans_no_matching_customer_removed", orphan_count)

    null_principal = df["principal_amount"].isna().sum()
    df = df[df["principal_amount"].notna()]
    log_issue("loans", "null_principal_amount_removed", null_principal)

    neg_rate = (df["interest_rate"] < 0).sum()
    df["interest_rate"] = df["interest_rate"].abs()
    log_issue("loans", "negative_interest_rate_corrected_to_absolute", neg_rate)

    null_tenor = df["tenor_months"].isna().sum()
    df["tenor_months"] = df["tenor_months"].fillna(df["tenor_months"].median())
    log_issue("loans", "missing_tenor_months_imputed_with_median", null_tenor)

    df["disbursement_date"] = pd.to_datetime(df["disbursement_date"], errors="coerce")
    bad_dates = df["disbursement_date"].isna().sum()
    log_issue("loans", "invalid_disbursement_date", bad_dates)

    df["days_past_due"] = df["days_past_due"].clip(lower=0)

    valid_statuses = {"Active", "Closed", "Written Off"}
    bad_status = (~df["loan_status"].isin(valid_statuses)).sum()
    log_issue("loans", "unrecognized_loan_status", bad_status)

    return df.reset_index(drop=True)



def clean_repayments(df, valid_loan_ids):
    before = len(df)
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")
    log_issue("repayments", "duplicate_transaction_id_removed", before - len(df))

    orphan_mask = ~df["loan_id"].isin(valid_loan_ids)
    orphan_count = orphan_mask.sum()
    df = df[~orphan_mask]
    log_issue("repayments", "orphan_repayments_no_matching_loan_removed", orphan_count)

    null_amount = df["amount_paid"].isna().sum()
    df = df[df["amount_paid"].notna()]
    log_issue("repayments", "null_amount_paid_removed", null_amount)

    neg_amount = (df["amount_paid"] < 0).sum()
    df["amount_paid"] = df["amount_paid"].abs()
    log_issue("repayments", "negative_amount_paid_corrected_to_absolute", neg_amount)

    df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
    bad_dates = df["payment_date"].isna().sum()
    log_issue("repayments", "invalid_payment_date", bad_dates)

    return df.reset_index(drop=True)


def main():
    customers = pd.read_csv("data/customers_raw.csv")
    loans = pd.read_csv("data/loans_raw.csv")
    repayments = pd.read_csv("data/repayments_raw.csv")

    customers_clean = clean_customers(customers)
    loans_clean = clean_loans(loans, set(customers_clean["customer_id"]))
    repayments_clean = clean_repayments(repayments, set(loans_clean["loan_id"]))

    customers_clean.to_csv("data/customers_clean.csv", index=False)
    loans_clean.to_csv("data/loans_clean.csv", index=False)
    repayments_clean.to_csv("data/repayments_clean.csv", index=False)

    report = pd.DataFrame(ISSUES)
    report.to_csv("data/data_quality_report.csv", index=False)

    print("\n--- Summary ---")
    print(f"customers: {len(customers)} -> {len(customers_clean)}")
    print(f"loans:     {len(loans)} -> {len(loans_clean)}")
    print(f"repayments:{len(repayments)} -> {len(repayments_clean)}")
    print(f"Total data-quality issues logged: {len(report)}")


if __name__ == "__main__":
    main()
