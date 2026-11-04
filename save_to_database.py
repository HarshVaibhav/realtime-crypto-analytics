"""Fetch one cryptocurrency snapshot and append it to SQL Server."""

from fetch import fetch
from db_connection import engine


def save_to_database():
    crypto_df = fetch()

    if crypto_df is None or crypto_df.empty:
        print("No cryptocurrency data available.")
        return

    try:
        # SQL Server DATETIME2 has no timezone field.
        # Keep the value in UTC, then remove timezone metadata.
        crypto_df["timestamp"] = (
            crypto_df["timestamp"]
            .dt.tz_convert("UTC")
            .dt.tz_localize(None)
        )

        print("\nData prepared for SQL Server:")
        print(crypto_df)

        with engine.begin() as connection:
            crypto_df.to_sql(
                name="CryptoPriceHistory",
                con=connection,
                schema="dbo",
                if_exists="append",
                index=False,
            )

        print("\nSuccessfully inserted records into SQL Server!")
        print("Total records inserted:", len(crypto_df))

    except Exception as error:
        print("\nDatabase insertion failed:")
        print(error)


if __name__ == "__main__":
    try:
        save_to_database()
    finally:
        engine.dispose()
