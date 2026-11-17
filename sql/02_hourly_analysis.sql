/*
Project: Real-Time Crypto Market Analytics
View: dbo.vw_CryptoHourlyAnalysis
Database: CryptoAnalyticsDB
Source: dbo.CryptoPriceHistory

Purpose:
- Aggregate observations into hourly buckets per cryptocurrency.
- Calculate hourly average price and observation count.
- Compare each hourly average with the previous available hourly bucket.
- Calculate absolute and percentage price movement.

Important:
LAG() compares with the previous AVAILABLE hourly bucket.
If collection has gaps, this is not necessarily a one-clock-hour return.
*/

USE CryptoAnalyticsDB;
GO

CREATE OR ALTER VIEW dbo.vw_CryptoHourlyAnalysis
AS
WITH HourlyData AS
(
    SELECT
        coin,
        DATEADD(HOUR, DATEDIFF(HOUR, 0, [timestamp]), 0)
            AS hour_bucket,
        AVG(price) AS avg_price,
        COUNT(*) AS total_records
    FROM dbo.CryptoPriceHistory
    GROUP BY
        coin,
        DATEADD(HOUR, DATEDIFF(HOUR, 0, [timestamp]), 0)
),
PriceMovement AS
(
    SELECT
        coin,
        hour_bucket,
        avg_price,
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

-- Verify the view.
SELECT *
FROM dbo.vw_CryptoHourlyAnalysis
ORDER BY coin, hour_bucket;
GO
