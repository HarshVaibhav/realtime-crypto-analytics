/*
Project: Real-Time Crypto Market Analytics
Purpose: Create the local database, source table, and duplicate-protection index.

Run this script in SSMS using an account allowed to create databases.
If the table already exists, this script leaves its data unchanged.
The unique index creation will fail if duplicate (coin, timestamp) keys exist;
resolve those duplicates before rerunning the script.
*/

IF DB_ID(N'CryptoAnalyticsDB') IS NULL
BEGIN
    EXEC(N'CREATE DATABASE CryptoAnalyticsDB');
END;
GO

USE CryptoAnalyticsDB;
GO

IF OBJECT_ID(N'dbo.CryptoPriceHistory', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CryptoPriceHistory
    (
        id BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_CryptoPriceHistory PRIMARY KEY,
        coin VARCHAR(50) NOT NULL,
        price DECIMAL(18,8) NOT NULL,
        chg_24h DECIMAL(12,6) NULL,
        [timestamp] DATETIME2(3) NOT NULL,
        created_at DATETIME2(3) NOT NULL
            CONSTRAINT DF_CryptoPriceHistory_created_at
            DEFAULT SYSUTCDATETIME()
    );
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CryptoPriceHistory')
      AND name = N'UX_CryptoPriceHistory_Coin_Timestamp'
)
BEGIN
    CREATE UNIQUE INDEX UX_CryptoPriceHistory_Coin_Timestamp
    ON dbo.CryptoPriceHistory (coin, [timestamp]);
END;
GO

-- Verify table and index setup.
EXEC sys.sp_help N'dbo.CryptoPriceHistory';
EXEC sys.sp_helpindex N'dbo.CryptoPriceHistory';
GO
