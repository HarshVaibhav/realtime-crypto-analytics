/*
Project: Real-Time Crypto Analytics Pipeline
File: Day 8 - Hourly cryptocurrency analysis
Database: CryptoAnalyticsDB
Source table: dbo.CryptoPriceHistory

Purpose:
- Aggregate collected observations into hourly buckets per cryptocurrency.
- Calculate hourly average, minimum, maximum, and observation count.
- Compare each hourly average with the previous available hourly bucket.
- Calculate absolute and percentage price movement.

Important:
LAG() compares with the previous AVAILABLE hourly bucket for that coin.
If collection has gaps, this is not necessarily a one-clock-hour return.
The first available bucket per coin has NULL previous price and movement.
*/

USE CryptoAnalyticsDB;
GO

CREATE OR ALTER VIEW dbo.vw_CryptoHourlyAnalysis
AS
WITH HourlyData AS
(
    SELECT
        coin,
        DATEADD(
            HOUR,
            DATEDIFF(HOUR, 0, [timestamp]),
            0
        ) AS hour_bucket,
        AVG(price) AS avg_price,
        MIN(price) AS min_price,
        MAX(price) AS max_price,
        COUNT(*) AS total_records
    FROM dbo.CryptoPriceHistory
    GROUP BY
        coin,
        DATEADD(
            HOUR,
            DATEDIFF(HOUR, 0, [timestamp]),
            0
        )
),
PriceMovement AS
(
    SELECT
        coin,
        hour_bucket,
        avg_price,
        min_price,
        max_price,
        total_records,
        LAG(avg_price) OVER (
            PARTITION BY coin
            ORDER BY hour_bucket
        ) AS previous_hour_avg_price
    FROM HourlyData
)
SELECT
    coin,
    hour_bucket,
    avg_price,
    min_price,
    max_price,
    previous_hour_avg_price,
    avg_price - previous_hour_avg_price AS price_difference,
    ROUND(
        (avg_price - previous_hour_avg_price)
        / NULLIF(previous_hour_avg_price, 0) * 100,
        4
    ) AS price_change_pct,
    total_records
FROM PriceMovement;
GO

-- Verify the view after creation.
SELECT *
FROM dbo.vw_CryptoHourlyAnalysis
ORDER BY coin, hour_bucket;
GO
