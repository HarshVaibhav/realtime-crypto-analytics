"""Database insertion helpers for cryptocurrency snapshots."""

import pandas as pd
from sqlalchemy import text


REQUIRED_COLUMNS = ["coin", "price", "chg_24h", "timestamp"]

INSERT_IF_MISSING = text("""
    INSERT INTO dbo.CryptoPriceHistory (coin, price, chg_24h, timestamp)
    SELECT :coin, :price, :chg_24h, :timestamp
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.CryptoPriceHistory WITH (UPDLOCK, HOLDLOCK)
        WHERE coin = :coin
          AND timestamp = :timestamp
    );
""")


def insert_snapshot(connection, dataframe):
    """Insert only observations not already present in the target table.

    SQL Server generates id and created_at. The unique index on
    (coin, timestamp) remains the final database-level duplicate safeguard.
    """
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(
            "Snapshot is missing required columns: "
            + ", ".join(missing_columns)
        )

    table_exists = connection.dialect.has_table(
        connection,
        "CryptoPriceHistory",
        schema="dbo",
    )
    if not table_exists:
        raise RuntimeError(
            "Required table dbo.CryptoPriceHistory does not exist. "
            "Create the source table before inserting data."
        )

    records = (
        dataframe[REQUIRED_COLUMNS]
        .astype(object)
        .where(pd.notna(dataframe[REQUIRED_COLUMNS]), None)
        .to_dict(orient="records")
    )

    inserted = 0
    skipped = 0

    for record in records:
        timestamp = record["timestamp"]
        if isinstance(timestamp, pd.Timestamp):
            record["timestamp"] = timestamp.to_pydatetime()

        result = connection.execute(INSERT_IF_MISSING, record)
        if result.rowcount == 1:
            inserted += 1
        else:
            skipped += 1

    return inserted, skipped
