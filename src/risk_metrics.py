"""
risk_metrics.py
----------------
Reusable portfolio risk metric calculations: delinquency by bucket,
recovery rate, and average days past due (DPD). Used by both the
Streamlit dashboard (dashboard.py) and the standalone stakeholder
report generator (generate_report.py).
"""

import pandas as pd

DPD_BUCKETS = [
    (0, 0, "0 - Current"),
    (1, 30, "1-30 DPD"),
    (31, 60, "31-60 DPD"),
    (61, 90, "61-90 DPD"),
    (91, float("inf"), "90+ DPD"),
]


def assign_bucket(dpd):
    for lo, hi, label in DPD_BUCKETS:
        if lo <= dpd <= hi:
            return label
    return "90+ DPD"


def delinquency_by_bucket(loans_df):
    active = loans_df[loans_df["loan_status"] == "Active"].copy()
    active["dpd_bucket"] = active["days_past_due"].apply(assign_bucket)
    summary = active.groupby("dpd_bucket").agg(
        loan_count=("loan_id", "count"),
        total_exposure=("principal_amount", "sum"),
        avg_loan_size=("principal_amount", "mean"),
    ).reindex([b[2] for b in DPD_BUCKETS]).fillna(0)
    summary["pct_of_portfolio"] = 100 * summary["loan_count"] / summary["loan_count"].sum()
    return summary.reset_index()


def delinquency_by_segment(loans_df, customers_df):
    merged = loans_df.merge(customers_df, on="customer_id", how="left")
    active = merged[merged["loan_status"] == "Active"]
    grp = active.groupby("segment").agg(
        total_loans=("loan_id", "count"),
        delinquent_loans=("days_past_due", lambda x: (x > 0).sum()),
    )
    grp["delinquency_rate_pct"] = 100 * grp["delinquent_loans"] / grp["total_loans"]
    return grp.reset_index().sort_values("delinquency_rate_pct", ascending=False)


def recovery_rate(loans_df, repayments_df):
    repaid = repayments_df.groupby("loan_id")["amount_paid"].sum().rename("total_repaid")
    merged = loans_df.merge(repaid, on="loan_id", how="left").fillna({"total_repaid": 0})
    overall = 100 * merged["total_repaid"].sum() / merged["principal_amount"].sum()
    by_type = merged.groupby("loan_type").apply(
        lambda g: 100 * g["total_repaid"].sum() / g["principal_amount"].sum()
    ).rename("recovery_rate_pct").reset_index()
    return overall, by_type


def avg_dpd(loans_df):
    active = loans_df[loans_df["loan_status"] == "Active"]
    overall = active["days_past_due"].mean()
    by_type = active.groupby("loan_type")["days_past_due"].mean().rename(
        "avg_dpd").reset_index().sort_values("avg_dpd", ascending=False)
    return overall, by_type


def monthly_collections(repayments_df):
    df = repayments_df.copy()
    df["payment_date"] = pd.to_datetime(df["payment_date"])
    df["month"] = df["payment_date"].dt.to_period("M").astype(str)
    return df.groupby("month")["amount_paid"].sum().reset_index().rename(
        columns={"amount_paid": "total_collected"})
