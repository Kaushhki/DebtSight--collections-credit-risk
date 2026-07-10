import sys
import os
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from risk_metrics import (
    delinquency_by_bucket,
    delinquency_by_segment,
    recovery_rate,
    avg_dpd,
    monthly_collections,
)

st.set_page_config(page_title="Collections & Credit Risk Dashboard", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data
def load_data():
    customers = pd.read_csv(os.path.join(DATA_DIR, "customers_clean.csv"))
    loans = pd.read_csv(os.path.join(DATA_DIR, "loans_clean.csv"))
    repayments = pd.read_csv(os.path.join(DATA_DIR, "repayments_clean.csv"))
    return customers, loans, repayments


customers, loans, repayments = load_data()

st.title("📊 Collections & Credit Risk Dashboard")
st.caption(
    "Tracks collections performance, delinquency rates, and overdue-loan "
    "trends across customer segments. Data is cleaned and validated "
    "upstream by src/data_cleaning.py."
)

with st.sidebar:
    st.header("Filters")
    segments = st.multiselect(
        "Customer segment", sorted(customers["segment"].unique()),
        default=sorted(customers["segment"].unique())
    )
    loan_types = st.multiselect(
        "Loan type", sorted(loans["loan_type"].unique()),
        default=sorted(loans["loan_type"].unique())
    )
    states = st.multiselect(
        "State", sorted(customers["state"].unique()),
        default=sorted(customers["state"].unique())
    )

filtered_customers = customers[
    customers["segment"].isin(segments) & customers["state"].isin(states)
]
filtered_loans = loans[
    loans["customer_id"].isin(filtered_customers["customer_id"])
    & loans["loan_type"].isin(loan_types)
]
filtered_repayments = repayments[repayments["loan_id"].isin(filtered_loans["loan_id"])]

active_loans = filtered_loans[filtered_loans["loan_status"] == "Active"]
total_exposure = active_loans["principal_amount"].sum()
delinquent_pct = 100 * (active_loans["days_past_due"] > 0).sum() / max(len(active_loans), 1)
overall_recovery, recovery_by_type = recovery_rate(filtered_loans, filtered_repayments)
overall_dpd, dpd_by_type = avg_dpd(filtered_loans)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Active Exposure", f"₹{total_exposure:,.0f}")
k2.metric("Delinquency Rate", f"{delinquent_pct:.1f}%")
k3.metric("Portfolio Recovery Rate", f"{overall_recovery:.1f}%")
k4.metric("Avg Days Past Due", f"{overall_dpd:.1f} days")

st.divider()


col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Delinquency by DPD Bucket")
    bucket_df = delinquency_by_bucket(filtered_loans)
    fig = px.bar(
        bucket_df, x="dpd_bucket", y="total_exposure",
        color="dpd_bucket", text_auto=".2s",
        labels={"total_exposure": "Exposure (₹)", "dpd_bucket": "DPD Bucket"},
        color_discrete_sequence=px.colors.sequential.OrRd,
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Loan Count by Bucket")
    fig2 = px.pie(bucket_df, names="dpd_bucket", values="loan_count", hole=0.45)
    st.plotly_chart(fig2, use_container_width=True)


st.subheader("Delinquency Rate by Customer Segment")
seg_df = delinquency_by_segment(filtered_loans, filtered_customers)
fig3 = px.bar(
    seg_df, x="segment", y="delinquency_rate_pct", color="segment",
    text_auto=".1f", labels={"delinquency_rate_pct": "Delinquency Rate (%)"},
)
fig3.update_layout(showlegend=False)
st.plotly_chart(fig3, use_container_width=True)


col3, col4 = st.columns(2)

with col3:
    st.subheader("Monthly Collections Trend")
    trend_df = monthly_collections(filtered_repayments)
    fig4 = px.line(trend_df, x="month", y="total_collected", markers=True)
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    st.subheader("Average DPD by Loan Type")
    fig5 = px.bar(
        dpd_by_type, x="loan_type", y="avg_dpd", color="loan_type",
        text_auto=".1f",
    )
    fig5.update_layout(showlegend=False)
    st.plotly_chart(fig5, use_container_width=True)

st.divider()


with st.expander("View filtered loan-level data"):
    st.dataframe(filtered_loans, use_container_width=True)

st.caption(
    "Data model: customers → loans → repayments (SQLite at data/collections.db). "
    "See sql/portfolio_risk_queries.sql for the equivalent SQL aggregations "
    "and src/data_cleaning.py for the validation pipeline."
)
