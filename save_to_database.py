"""Fetch one cryptocurrency snapshot, clean it, and append it to SQL Server."""

from fetch import fetch
from clean_data import clean_data
from db_connection import engine


def save_to_database():
    print("\n--- CRYPTO DATA PIPELINE ---")

    # 1. Fetch API data.
    print("\nStep 1: Fetching cryptocurrency data...")
    crypto_df = fetch()

    if crypto_df is None or crypto_df.empty:
        print("No data received. Database insertion skipped.")
        return

    print("Records fetched:", len(crypto_df))

    # 2. Clean and validate the data.
    print("\nStep 2: Cleaning cryptocurrency data...")
    cleaned_df = clean_data(crypto_df)

    if cleaned_df.empty:
        print("No valid records after cleaning.")
        return

    print("Valid records:", len(cleaned_df))

    # 3. SQL Server DATETIME2 has no timezone field.
    # Keep the timestamp in UTC, then remove timezone metadata.
    cleaned_df["timestamp"] = (
        cleaned_df["timestamp"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
    )

    # 4. Append cleaned records to the historical table.
    print("\nStep 3: Saving cleaned data to SQL Server...")

    try:
        with engine.begin() as connection:
            cleaned_df.to_sql(
                name="CryptoPriceHistory",
                con=connection,
                schema="dbo",
                if_exists="append",
                index=False,
            )

        print("\nDatabase insertion successful!")
        print("Records inserted:", len(cleaned_df))

    except Exception as error:
        print("\nDatabase insertion failed:")
        print(error)


if __name__ == "__main__":
    try:
        save_to_database()
    finally:
        engine.dispose()
