/*
  Bootstrap the Crypto Analytics database.
  Run this script in SSMS using an account allowed to create databases.
  Safe to rerun. Existing tables and data are not dropped or modified.
*/
IF DB_ID(N'CryptoAnalyticsDB') IS NULL
BEGIN
    CREATE DATABASE CryptoAnalyticsDB;
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
            CONSTRAINT DF_CryptoPriceHistory_CreatedAt
            DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_CryptoPriceHistory_Price_Positive CHECK (price > 0),
        CONSTRAINT CK_CryptoPriceHistory_Coin_NotBlank CHECK (LEN(LTRIM(RTRIM(coin))) > 0)
    );
END;
GO

/*
  A unique index is the final duplicate safeguard.
  Stop with a clear message rather than silently deleting historical data
  if the existing table already contains duplicate coin/timestamp pairs.
*/
IF EXISTS
(
    SELECT 1
    FROM dbo.CryptoPriceHistory
    GROUP BY coin, [timestamp]
    HAVING COUNT_BIG(*) > 1
)
BEGIN
    THROW 51000,
      'Duplicate (coin, timestamp) rows exist. Review and resolve them before creating the unique index. No data was deleted.',
      1;
END;
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CryptoPriceHistory')
      AND name = N'UX_CryptoPriceHistory_Coin_Timestamp'
)
BEGIN
    CREATE UNIQUE INDEX UX_CryptoPriceHistory_Coin_Timestamp
        ON dbo.CryptoPriceHistory (coin, [timestamp]);
END;
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.CryptoPriceHistory')
      AND name = N'IX_CryptoPriceHistory_Coin_Timestamp_Id'
)
BEGIN
    CREATE INDEX IX_CryptoPriceHistory_Coin_Timestamp_Id
        ON dbo.CryptoPriceHistory (coin, [timestamp], id)
        INCLUDE (price, chg_24h);
END;
GO

SELECT
    DB_NAME() AS database_name,
    OBJECT_ID(N'dbo.CryptoPriceHistory', N'U') AS source_table_id,
    (SELECT COUNT_BIG(*) FROM dbo.CryptoPriceHistory) AS existing_rows;
GO
