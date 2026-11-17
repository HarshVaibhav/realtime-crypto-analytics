/*
Project: Real-Time Crypto Market Analytics
View: dbo.vw_CryptoIntervalQuality
Database: CryptoAnalyticsDB
Source: dbo.CryptoPriceHistory

Purpose:
- Retrieve the previous observation timestamp per cryptocurrency.
- Calculate a collection interval classification.

Classification aligned with dbo.vw_CryptoAnalytics:
- First Observation: no previous timestamp.
- Short Interval: less than 240 seconds.
- Reliable Interval: 240–360 seconds (inclusive).
- Long Interval: more than 360 seconds.

The 240–360 second reliable range is based on the intended
five-minute collection cadence with a tolerance of one minute.
*/

USE CryptoAnalyticsDB;
GO

CREATE OR ALTER VIEW dbo.vw_CryptoIntervalQuality
AS
WITH PreviousData AS
(
    SELECT
        id,
        coin,
        [timestamp],
        LAG([timestamp]) OVER (
            PARTITION BY coin
            ORDER BY [timestamp], id
        ) AS previous_timestamp
    FROM dbo.CryptoPriceHistory
),
IntervalData AS
(
    SELECT
        id,
        coin,
        [timestamp],
        previous_timestamp,
        CASE
            WHEN previous_timestamp IS NULL
                THEN 'First Observation'
            WHEN DATEDIFF(SECOND, previous_timestamp, [timestamp]) < 240
                THEN 'Short Interval'
            WHEN DATEDIFF(SECOND, previous_timestamp, [timestamp]) <= 360
                THEN 'Reliable Interval'
            ELSE 'Long Interval'
        END AS interval_status
    FROM PreviousData
)
SELECT *
FROM IntervalData;
GO

-- Verify the interval classifications.
SELECT
    coin,
    interval_status,
    COUNT(*) AS total_records
FROM dbo.vw_CryptoIntervalQuality
GROUP BY coin, interval_status
ORDER BY coin, interval_status;
GO
