/*
Project: Real-Time Crypto Market Analytics
View: dbo.vw_CryptoAnalytics
Database: CryptoAnalyticsDB
Source: dbo.CryptoPriceHistory

Purpose:
- Calculate previous price and timestamp per cryptocurrency.
- Calculate a 3-observation moving average.
- Classify collection intervals.
- Calculate reliable-interval returns and snapshot returns.
- Calculate average return, return standard deviation, Z-score,
  and an exploratory anomaly status.

Reliable interval definition: 240–360 seconds (inclusive).
Snapshot returns are not CoinGecko's API-reported 24-hour change.
*/

USE CryptoAnalyticsDB;
GO

CREATE OR ALTER VIEW dbo.vw_CryptoAnalytics
AS
WITH PriceHistory AS
(
    SELECT
        id,
        coin,
        price,
        chg_24h,
        [timestamp],
        LAG(price) OVER (
            PARTITION BY coin
            ORDER BY [timestamp], id
        ) AS previous_price,
        LAG([timestamp]) OVER (
            PARTITION BY coin
            ORDER BY [timestamp], id
        ) AS previous_timestamp,
        AVG(price) OVER (
            PARTITION BY coin
            ORDER BY [timestamp], id
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS moving_avg_3
    FROM dbo.CryptoPriceHistory
),
IntervalAnalysis AS
(
    SELECT
        *,
        DATEDIFF(SECOND, previous_timestamp, [timestamp])
            AS interval_seconds
    FROM PriceHistory
),
IntervalClassification AS
(
    SELECT
        *,
        CASE
            WHEN previous_timestamp IS NULL
                THEN 'First Observation'
            WHEN interval_seconds BETWEEN 240 AND 360
                THEN 'Reliable Interval'
            WHEN interval_seconds < 240
                THEN 'Short Interval'
            ELSE 'Long Interval'
        END AS interval_status
    FROM IntervalAnalysis
),
SnapshotReturns AS
(
    SELECT
        *,
        CASE
            WHEN interval_status = 'Reliable Interval'
            THEN
                (price - previous_price) * 100.0
                / NULLIF(previous_price, 0)
            ELSE NULL
        END AS reliable_return_pct,
        (price - previous_price) * 100.0
            / NULLIF(previous_price, 0) AS snapshot_return_pct
    FROM IntervalClassification
),
ReturnStatistics AS
(
    SELECT
        *,
        AVG(reliable_return_pct) OVER (
            PARTITION BY coin
        ) AS average_return,
        STDEV(reliable_return_pct) OVER (
            PARTITION BY coin
        ) AS return_stddev
    FROM SnapshotReturns
)
SELECT
    id,
    coin,
    [timestamp],
    price,
    chg_24h,
    previous_price,
    previous_timestamp,
    interval_seconds,
    interval_status,
    reliable_return_pct,
    snapshot_return_pct,
    moving_avg_3,
    average_return,
    return_stddev,
    (reliable_return_pct - average_return)
        / NULLIF(return_stddev, 0) AS z_score,
    CASE
        WHEN reliable_return_pct IS NULL OR return_stddev IS NULL
            THEN 'Insufficient History'
        WHEN return_stddev = 0
            THEN 'No Variation'
        WHEN ABS(
            (reliable_return_pct - average_return)
            / NULLIF(return_stddev, 0)
        ) >= 2
            THEN 'Potential Anomaly'
        ELSE 'Normal'
    END AS anomaly_status
FROM ReturnStatistics;
GO

-- Verify the view.
SELECT TOP (20) *
FROM dbo.vw_CryptoAnalytics
ORDER BY coin, [timestamp] DESC, id DESC;
GO
