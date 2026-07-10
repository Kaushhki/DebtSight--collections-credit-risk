# Collections & Credit Risk Dashboard

An end-to-end collections and credit-risk analytics pipeline: synthetic loan
portfolio data → automated cleaning & validation → SQL aggregation →
interactive dashboard, with a stakeholder-ready summary report generated
alongside it.

**[Live Dashboard →](#deployment)** https://debtsight--collections-credit-risk-dqiogtakhxt32xd8enuo2b.streamlit.app/

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![SQLite](https://img.shields.io/badge/SQL-SQLite-lightgrey)

---

## What this project does

Loan collections teams need to know, at a glance: *who's overdue, how much
is at risk, how much are we actually recovering, and is it getting better
or worse by segment.* This project builds that pipeline from raw (messy)
data to a stakeholder-facing dashboard:

1. **Generate/ingest data** — synthetic customer, loan, and repayment
   transaction data, intentionally seeded with realistic data-quality
   issues (duplicates, nulls, negative values, orphan records).
2. **Clean & validate** — a rule-based, auditable pipeline that catches
   and logs every issue rather than silently dropping rows.
3. **Aggregate with SQL** — the cleaned data is loaded into SQLite and
   queried directly with SQL for portfolio-level metrics.
4. **Visualize** — an interactive Streamlit dashboard tracking delinquency,
   recovery rate, and overdue-loan trends across customer segments.
5. **Report** — a standalone script produces a stakeholder summary CSV
   without requiring anyone to open the dashboard.

## Dashboard features

- **KPI header**: active exposure, delinquency rate, portfolio recovery
  rate, average days past due (DPD)
- **Delinquency by DPD bucket** (Current / 1-30 / 31-60 / 61-90 / 90+),
  by exposure and by loan count
- **Delinquency rate by customer segment** (Retail, SME, Corporate, Agri,
  Microfinance)
- **Monthly collections trend**
- **Average DPD by loan type**
- **Filters**: segment, loan type, state — all charts update live
- Drill-down into filtered loan-level data

## Tech stack

| Layer              | Tool                          |
|--------------------|--------------------------------|
| Data generation     | Python (pandas, numpy)        |
| Cleaning/validation | Python (pandas)                |
| Aggregation         | SQL (SQLite)                   |
| Dashboard           | Streamlit + Plotly             |
| Reporting           | Python (pandas → CSV)          |

> **Note on Power BI:** the original version of this project used Power BI
> for visualization. This repo ports the same data model and metrics to a
> Streamlit dashboard instead, since it's git-friendly, requires no
> licensed desktop software to view, and can be deployed as a live link
> (see [Deployment](#deployment)) rather than a static `.pbix` file. The
> underlying `data/collections.db` SQLite database and cleaned CSVs plug
> directly into Power BI's "Get Data" if you want to rebuild the Power BI
> version — the data model (customers → loans → repayments) is identical.

## Project structure

```
collections-credit-risk/
├── dashboard.py                    # Streamlit app (entry point)
├── requirements.txt
├── data/
│   ├── customers_raw.csv / customers_clean.csv
│   ├── loans_raw.csv / loans_clean.csv
│   ├── repayments_raw.csv / repayments_clean.csv
│   ├── data_quality_report.csv     # audit log of every cleaning rule applied
│   ├── stakeholder_risk_report.csv # combined summary report
│   └── collections.db              # SQLite DB used for SQL aggregation
├── src/
│   ├── generate_data.py            # synthetic data generator
│   ├── data_cleaning.py            # cleaning & validation pipeline
│   ├── load_to_sql.py              # loads clean CSVs into SQLite
│   ├── risk_metrics.py             # shared metric calculations
│   └── generate_report.py          # standalone stakeholder report
└── sql/
    └── portfolio_risk_queries.sql  # delinquency, recovery, DPD, trend queries
```

## Data model

```
customers (customer_id, segment, state, credit_score, onboarding_date)
        │
        │ 1-to-many
        ▼
loans (loan_id, customer_id, loan_type, principal_amount, interest_rate,
       tenor_months, disbursement_date, days_past_due, loan_status)
        │
        │ 1-to-many
        ▼
repayments (transaction_id, loan_id, payment_date, amount_paid, payment_method)
```

## Data cleaning & validation

`src/data_cleaning.py` runs a series of standalone, composable checks per
table and logs every affected row to `data/data_quality_report.csv` for
audit — nothing is silently dropped. Rules applied:

- Duplicate record removal (`customer_id`, `loan_id`, `transaction_id`)
- Orphan record detection (loans/repayments with no matching parent)
- Null handling: median imputation for numeric fields, row removal for
  fields with no safe default (e.g. principal amount)
- Range validation and correction (credit score clipped to 300-900,
  negative interest rates / payment amounts corrected)
- Date parsing and validation

On the current synthetic dataset this catches **16 distinct data-quality
issues across ~230 affected rows** — duplicates, orphans, nulls, and
invalid values — before the data ever reaches the dashboard or SQL layer.

## Running locally

```bash
git clone https://github.com/<your-username>/collections-credit-risk.git
cd collections-credit-risk
pip install -r requirements.txt

# Optional — regenerate data from scratch (raw + clean CSVs are already
# included in the repo, so this step is optional)
python src/generate_data.py
python src/data_cleaning.py
python src/load_to_sql.py

# Generate the stakeholder summary report
python src/generate_report.py

# Launch the dashboard
streamlit run dashboard.py
```

## SQL queries

All portfolio aggregation queries live in
[`sql/portfolio_risk_queries.sql`](sql/portfolio_risk_queries.sql):
delinquency by bucket, delinquency rate by segment, portfolio recovery
rate, average DPD by loan type, monthly collections trend, and top-risk
states by 90+ DPD exposure. Written in standard ANSI SQL against SQLite,
portable to Postgres/MySQL/SQL Server for a production loan book.

## Deployment

To deploy the live dashboard on Streamlit Cloud:
1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io), connect your
   GitHub account, and select this repo with `dashboard.py` as the entry
   point.
3. Add the deployed link back into this README.

## Possible extensions

- Swap SQLite for a Postgres instance for concurrent multi-user access
- Add a scheduled ingestion job (e.g. Airflow/cron) to refresh data daily
- Add cohort-based vintage analysis (delinquency by disbursement month)
- Add an XGBoost/logistic regression default-risk scoring model
