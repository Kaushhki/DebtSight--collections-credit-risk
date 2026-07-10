
SELECT
    CASE
        WHEN days_past_due = 0 THEN '0 - Current'
        WHEN days_past_due BETWEEN 1 AND 30 THEN '1-30 DPD'
        WHEN days_past_due BETWEEN 31 AND 60 THEN '31-60 DPD'
        WHEN days_past_due BETWEEN 61 AND 90 THEN '61-90 DPD'
        ELSE '90+ DPD'
    END AS dpd_bucket,
    COUNT(*)                       AS loan_count,
    ROUND(SUM(principal_amount), 2) AS total_exposure,
    ROUND(AVG(principal_amount), 2) AS avg_loan_size
FROM loans
WHERE loan_status = 'Active'
GROUP BY dpd_bucket
ORDER BY MIN(days_past_due);



SELECT
    c.segment,
    COUNT(l.loan_id)                                              AS total_loans,
    SUM(CASE WHEN l.days_past_due > 0 THEN 1 ELSE 0 END)          AS delinquent_loans,
    ROUND(100.0 * SUM(CASE WHEN l.days_past_due > 0 THEN 1 ELSE 0 END)
          / COUNT(l.loan_id), 2)                                  AS delinquency_rate_pct
FROM loans l
JOIN customers c ON c.customer_id = l.customer_id
WHERE l.loan_status = 'Active'
GROUP BY c.segment
ORDER BY delinquency_rate_pct DESC;



SELECT
    ROUND(100.0 * SUM(r.total_repaid) / SUM(l.principal_amount), 2) AS portfolio_recovery_rate_pct
FROM loans l
LEFT JOIN (
    SELECT loan_id, SUM(amount_paid) AS total_repaid
    FROM repayments
    GROUP BY loan_id
) r ON r.loan_id = l.loan_id;



SELECT
    loan_type,
    ROUND(AVG(days_past_due), 1) AS avg_dpd,
    COUNT(*)                     AS loan_count
FROM loans
WHERE loan_status = 'Active'
GROUP BY loan_type
ORDER BY avg_dpd DESC;



SELECT
    strftime('%Y-%m', payment_date) AS collection_month,
    ROUND(SUM(amount_paid), 2)      AS total_collected,
    COUNT(DISTINCT loan_id)         AS loans_touched
FROM repayments
GROUP BY collection_month
ORDER BY collection_month;



SELECT
    c.state,
    COUNT(l.loan_id)                AS loans_90plus,
    ROUND(SUM(l.principal_amount),2) AS exposure_90plus
FROM loans l
JOIN customers c ON c.customer_id = l.customer_id
WHERE l.days_past_due > 90 AND l.loan_status = 'Active'
GROUP BY c.state
ORDER BY exposure_90plus DESC
LIMIT 10;
