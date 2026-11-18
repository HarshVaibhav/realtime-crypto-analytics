/*
Project: Real-Time Crypto Market Analytics
Purpose: Generate reproducible, data-backed findings for the README/report.

Run after:
  00_create_database.sql
  01_crypto_analytics.sql
  02_hourly_analysis.sql
  03_interval_quality.sql

This script is read-only. It does not modify source data or views.
*/
USE CryptoAnalyticsDB;
GO

-- 1. Coverage and observed price movement by cryptocurrency.
WITH Ranked AS
(
    SELECT
        coin,
        [timestamp],
        price,
        ROW_NUMBER() OVER (PARTITION BY coin ORDER BY [timestamp], id) AS first_row,
        ROW_NUMBER() OVER (PARTITION BY coin ORDER BY [timestamp] DESC, id DESC) AS last_row
    FROM dbo.CryptoPriceHistory
),
Coverage AS
(
    SELECT
        coin,
        COUNT_BIG(*) AS observation_count,
        MIN([timestamp]) AS first_observation_utc,
        MAX([timestamp]) AS latest_observation_utc,
        MAX(CASE WHEN first_row = 1 THEN price END) AS first_observed_price,
        MAX(CASE WHEN last_row = 1 THEN price END) AS latest_observed_price,
        MAX(CASE WHEN last_row = 1 THEN [timestamp] END) AS latest_timestamp_utc,
        MAX(price) AS highest_observed_price,
        MIN(price) AS lowest_observed_price
    FROM Ranked
    GROUP BY coin
)
SELECT
    coin,
    observation_count,
    first_observation_utc,
    latest_observation_utc,
    DATEDIFF(MINUTE, first_observation_utc, latest_observation_utc) AS observed_span_minutes,
    first_observed_price,
    latest_observed_price,
    CAST(
        (latest_observed_price - first_observed_price) * 100.0
        / NULLIF(first_observed_price, 0)
        AS DECIMAL(18, 4)
    ) AS first_to_latest_change_pct,
    highest_observed_price,
    lowest_observed_price
FROM Coverage
ORDER BY coin;
GO

-- 2. Collection interval quality. First observations are excluded because
-- they have no previous observation to compare against.
SELECT
    coin,
    COUNT_BIG(*) AS total_observations,
    SUM(CASE WHEN interval_status IN ('Reliable Interval', 'Short Interval', 'Long Interval')
             THEN 1 ELSE 0 END) AS comparable_intervals,
    SUM(CASE WHEN interval_status = 'Reliable Interval' THEN 1 ELSE 0 END) AS reliable_intervals,
    SUM(CASE WHEN interval_status = 'Short Interval' THEN 1 ELSE 0 END) AS short_intervals,
    SUM(CASE WHEN interval_status = 'Long Interval' THEN 1 ELSE 0 END) AS long_intervals,
    CAST(
        100.0 * SUM(CASE WHEN interval_status = 'Reliable Interval' THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN interval_status IN ('Reliable Interval', 'Short Interval', 'Long Interval')
                          THEN 1 ELSE 0 END), 0)
        AS DECIMAL(8, 2)
    ) AS reliable_interval_rate_pct
FROM dbo.vw_CryptoAnalytics
GROUP BY coin
ORDER BY coin;
GO

-- 3. Return distribution for comparable (reliable-interval) snapshots.
SELECT
    coin,
    COUNT(reliable_return_pct) AS reliable_return_observations,
    CAST(AVG(reliable_return_pct) AS DECIMAL(18, 6)) AS average_reliable_snapshot_return_pct,
    CAST(STDEV(reliable_return_pct) AS DECIMAL(18, 6)) AS reliable_snapshot_return_stddev_pct,
    CAST(MIN(reliable_return_pct) AS DECIMAL(18, 6)) AS minimum_reliable_snapshot_return_pct,
    CAST(MAX(reliable_return_pct) AS DECIMAL(18, 6)) AS maximum_reliable_snapshot_return_pct
FROM dbo.vw_CryptoAnalytics
GROUP BY coin
ORDER BY coin;
GO

-- 4. Potential anomalies flagged by the rolling, prior-observation baseline.
-- These are review candidates, not confirmed market events or data errors.
SELECT TOP (25)
    coin,
    [timestamp],
    price,
    reliable_return_pct,
    prior_return_count,
    prior_average_return,
    prior_return_stddev,
    rolling_z_score,
    anomaly_status
FROM dbo.vw_CryptoAnalytics
WHERE anomaly_status = 'Potential Anomaly'
ORDER BY ABS(rolling_z_score) DESC, [timestamp] DESC;
GO

-- 5. Most recent observation per coin, including API-reported 24-hour change.
WITH Latest AS
(
    SELECT
        coin,
        [timestamp],
        price,
        chg_24h,
        ROW_NUMBER() OVER (PARTITION BY coin ORDER BY [timestamp] DESC, id DESC) AS rn
    FROM dbo.CryptoPriceHistory
)
SELECT
    coin,
    [timestamp] AS latest_observation_utc,
    price AS latest_observed_price_usd,
    chg_24h AS api_reported_24h_change_pct
FROM Latest
WHERE rn = 1
ORDER BY coin;
GO
