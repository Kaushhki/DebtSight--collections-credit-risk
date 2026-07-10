"""
generate_report.py
-------------------
Produces a standalone stakeholder summary report (CSV + printed console
summary) covering delinquency by bucket, recovery rate, and average DPD
-- for stakeholders who just want the numbers, not the live dashboard.

Run:
    python src/generate_report.py
Outputs:
    data/stakeholder_risk_report.csv
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from risk_metrics import (
    delinquency_by_bucket,
    delinquency_by_segment,
    recovery_rate,
    avg_dpd,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def main():
    customers = pd.read_csv(os.path.join(DATA_DIR, "customers_clean.csv"))
    loans = pd.read_csv(os.path.join(DATA_DIR, "loans_clean.csv"))
    repayments = pd.read_csv(os.path.join(DATA_DIR, "repayments_clean.csv"))

    bucket_df = delinquency_by_bucket(loans)
    segment_df = delinquency_by_segment(loans, customers)
    overall_recovery, recovery_by_type = recovery_rate(loans, repayments)
    overall_dpd, dpd_by_type = avg_dpd(loans)

    print("=" * 60)
    print("COLLECTIONS & CREDIT RISK — STAKEHOLDER SUMMARY")
    print("=" * 60)
    print(f"\nPortfolio Recovery Rate: {overall_recovery:.2f}%")
    print(f"Average Days Past Due:   {overall_dpd:.1f} days\n")

    print("-- Delinquency by DPD Bucket --")
    print(bucket_df.to_string(index=False))

    print("\n-- Delinquency Rate by Segment --")
    print(segment_df.to_string(index=False))

    print("\n-- Recovery Rate by Loan Type --")
    print(recovery_by_type.to_string(index=False))

    print("\n-- Average DPD by Loan Type --")
    print(dpd_by_type.to_string(index=False))

    # Combine into a single exportable report
    bucket_df.insert(0, "report_section", "delinquency_by_bucket")
    segment_df.insert(0, "report_section", "delinquency_by_segment")
    recovery_by_type.insert(0, "report_section", "recovery_by_loan_type")
    dpd_by_type.insert(0, "report_section", "avg_dpd_by_loan_type")

    combined = pd.concat(
        [bucket_df, segment_df, recovery_by_type, dpd_by_type],
        ignore_index=True, sort=False
    )
    out_path = os.path.join(DATA_DIR, "stakeholder_risk_report.csv")
    combined.to_csv(out_path, index=False)
    print(f"\nSaved combined report -> {out_path}")


if __name__ == "__main__":
    main()
