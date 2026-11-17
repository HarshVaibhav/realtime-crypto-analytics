/*
Project: Real-Time Crypto Analytics Pipeline
File: Day 7 - SQL analysis practice
Database: CryptoAnalyticsDB
Source table: dbo.CryptoPriceHistory

Run each query separately in SSMS.
Snapshot returns compare consecutive collected observations; they are not 24-hour returns.
Use timestamp and id together for deterministic ordering when timestamps tie.
*/

-- TASK 1: Latest recorded price for each cryptocurrency
-- Concepts: CTE, ROW_NUMBER(), PARTITION BY
WITH LatestCryptoPrice AS (
    SELECT coin, price, [timestamp],
        ROW_NUMBER() OVER (
            PARTITION BY coin
            ORDER BY [timestamp] DESC, id DESC
        ) AS rn
    FROM dbo.CryptoPriceHistory
)
SELECT coin, price AS latest_price, [timestamp] AS latest_timestamp
FROM LatestCryptoPrice
WHERE rn = 1
ORDER BY coin;


-- TASK 2: Snapshot-to-snapshot percentage returns
-- Concepts: LAG(), PARTITION BY, NULLIF()
WITH CryptoReturns AS (
    SELECT id, coin, [timestamp], price,
        LAG(price) OVER (
            PARTITION BY coin
            ORDER BY [timestamp], id
        ) AS previous_price
    FROM dbo.CryptoPriceHistory
)
SELECT coin, [timestamp], price, previous_price,
    ((price - previous_price) / NULLIF(previous_price, 0)) * 100
        AS snapshot_return_pct
FROM CryptoReturns
ORDER BY coin, [timestamp], id;


-- TASK 3: Rolling 5- and 10-observation moving averages
-- Concepts: AVG() OVER(), ROWS frame
SELECT coin, [timestamp], id, price,
    AVG(price) OVER (
        PARTITION BY coin
        ORDER BY [timestamp], id
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS moving_avg_5,
    AVG(price) OVER (
        PARTITION BY coin
        ORDER BY [timestamp], id
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS moving_avg_10
FROM dbo.CryptoPriceHistory
ORDER BY coin, [timestamp], id;


-- TASK 4: Highest and lowest recorded prices per coin
-- Concepts: MAX(), MIN(), GROUP BY
SELECT coin,
    MAX(price) AS highest_price,
    MIN(price) AS lowest_price
FROM dbo.CryptoPriceHistory
GROUP BY coin
ORDER BY coin;


-- TASK 5: Rank cryptocurrencies by their latest API-reported 24-hour change
-- Concepts: CTE, ROW_NUMBER(), RANK()
-- This is chg_24h from the API, not a calculated snapshot return.
WITH LatestCryptoChange AS (
    SELECT coin, chg_24h, [timestamp], id,
        ROW_NUMBER() OVER (
            PARTITION BY coin
            ORDER BY [timestamp] DESC, id DESC
        ) AS rn
    FROM dbo.CryptoPriceHistory
)
SELECT coin, chg_24h,
    RANK() OVER (
        ORDER BY
            CASE WHEN chg_24h IS NULL THEN 1 ELSE 0 END,
            chg_24h DESC
    ) AS performance_rank
FROM LatestCryptoChange
WHERE rn = 1
ORDER BY performance_rank, coin;


-- TASK 6: Average snapshot return and return volatility
-- Concepts: LAG(), CTE, AVG(), STDEV()
-- STDEV() is SQL Server's sample standard deviation function.
WITH PreviousPrices AS (
    SELECT coin, [timestamp], id, price,
        LAG(price) OVER (
            PARTITION BY coin
            ORDER BY [timestamp], id
        ) AS previous_price
    FROM dbo.CryptoPriceHistory
),
CalculatedReturns AS (
    SELECT coin,
        ((price - previous_price) / NULLIF(previous_price, 0)) * 100
            AS snapshot_return_pct
    FROM PreviousPrices
)
SELECT coin,
    AVG(snapshot_return_pct) AS average_return_pct,
    STDEV(snapshot_return_pct) AS return_volatility_pct
FROM CalculatedReturns
WHERE snapshot_return_pct IS NOT NULL
GROUP BY coin
ORDER BY return_volatility_pct DESC;
