/*
Project: Real-Time Crypto Market Analytics
View: dbo.vw_CryptoAnalytics
Source: dbo.CryptoPriceHistory
Snapshot returns compare consecutive observations, not fixed five-minute
or 24-hour returns. Reliable interval is 240-360 seconds inclusive.
Anomaly baseline uses prior observations only, avoiding future-data leakage.
*/
USE CryptoAnalyticsDB;
GO
CREATE OR ALTER VIEW dbo.vw_CryptoAnalytics
AS
WITH PriceHistory AS
(
    SELECT id, coin, price, chg_24h, [timestamp],
        LAG(price) OVER (PARTITION BY coin ORDER BY [timestamp], id) AS previous_price,
        LAG([timestamp]) OVER (PARTITION BY coin ORDER BY [timestamp], id) AS previous_timestamp,
        AVG(price) OVER (PARTITION BY coin ORDER BY [timestamp], id ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3,
        AVG(price) OVER (PARTITION BY coin ORDER BY [timestamp], id ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS moving_avg_5,
        AVG(price) OVER (PARTITION BY coin ORDER BY [timestamp], id ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) AS moving_avg_10
    FROM dbo.CryptoPriceHistory
),
Intervals AS
(
    SELECT *, DATEDIFF(SECOND, previous_timestamp, [timestamp]) AS interval_seconds
    FROM PriceHistory
),
Classified AS
(
    SELECT *,
        CASE WHEN previous_timestamp IS NULL THEN 'First Observation'
             WHEN interval_seconds BETWEEN 240 AND 360 THEN 'Reliable Interval'
             WHEN interval_seconds < 240 THEN 'Short Interval'
             ELSE 'Long Interval' END AS interval_status
    FROM Intervals
),
Returns AS
(
    SELECT *,
        (price - previous_price) * 100.0 / NULLIF(previous_price, 0) AS snapshot_return_pct,
        CASE WHEN interval_status = 'Reliable Interval'
             THEN (price - previous_price) * 100.0 / NULLIF(previous_price, 0) END AS reliable_return_pct
    FROM Classified
),
Baseline AS
(
    SELECT *,
        COUNT(reliable_return_pct) OVER (
            PARTITION BY coin ORDER BY [timestamp], id ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
        ) AS prior_return_count,
        AVG(reliable_return_pct) OVER (
            PARTITION BY coin ORDER BY [timestamp], id ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
        ) AS prior_average_return,
        STDEV(reliable_return_pct) OVER (
            PARTITION BY coin ORDER BY [timestamp], id ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
        ) AS prior_return_stddev
    FROM Returns
)
SELECT id, coin, [timestamp], price, chg_24h, previous_price, previous_timestamp,
    interval_seconds, interval_status, snapshot_return_pct, reliable_return_pct,
    moving_avg_3, moving_avg_5, moving_avg_10,
    prior_return_count, prior_average_return, prior_return_stddev,
    CASE WHEN prior_return_count >= 10
         THEN (reliable_return_pct - prior_average_return) / NULLIF(prior_return_stddev, 0) END AS rolling_z_score,
    CASE WHEN reliable_return_pct IS NULL THEN 'Insufficient History'
         WHEN prior_return_count < 10 THEN 'Insufficient Baseline'
         WHEN prior_return_stddev IS NULL OR prior_return_stddev = 0 THEN 'Insufficient Variance'
         WHEN ABS((reliable_return_pct - prior_average_return) / NULLIF(prior_return_stddev, 0)) >= 3
              THEN 'Potential Anomaly'
         ELSE 'Normal' END AS anomaly_status
FROM Baseline;
GO

SELECT TOP (20) *
FROM dbo.vw_CryptoAnalytics
ORDER BY coin, [timestamp] DESC, id DESC;
GO
