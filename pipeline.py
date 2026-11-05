"""Run a two-cycle test of the five-minute crypto data pipeline."""

import logging
import time

from fetch import fetch
from clean_data import clean_data
from db_connection import engine

INTERVAL_SECONDS = 300
MAX_CYCLES = 2

logging.basicConfig(
    filename="pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run_pipeline():
    """Fetch, clean, and append one snapshot to SQL Server."""

    logging.info("Starting collection cycle.")
    print("\n--- NEW COLLECTION CYCLE ---")

    # STEP 1: Fetch API data.
    print("\nStep 1: Fetching data...")
    crypto_df = fetch()

    if crypto_df is None or crypto_df.empty:
        logging.error("No data received. Cycle failed.")
        print("No cryptocurrency data available.")
        return False

    print("Records fetched:", len(crypto_df))

    # STEP 2: Clean and validate data.
    print("\nStep 2: Cleaning data...")
    cleaned_df = clean_data(crypto_df)

    if cleaned_df.empty:
        logging.error("No valid records after cleaning.")
        print("No valid records. Database insertion skipped.")
        return False

    print("Valid records:", len(cleaned_df))

    # STEP 3: Prepare UTC timestamps for SQL Server DATETIME2.
    cleaned_df["timestamp"] = (
        cleaned_df["timestamp"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
    )

    # STEP 4: Append records to SQL Server.
    print("\nStep 3: Saving data to SQL Server...")

    try:
        with engine.begin() as connection:
            cleaned_df.to_sql(
                name="CryptoPriceHistory",
                con=connection,
                schema="dbo",
                if_exists="append",
                index=False,
            )

        logging.info(
            "Successfully inserted %s records.",
            len(cleaned_df),
        )
        print("Database insertion successful!")
        print("Records inserted:", len(cleaned_df))
        return True

    except Exception as error:
        logging.exception("Database insertion failed: %s", error)
        print("Database insertion failed:", error)
        return False


if __name__ == "__main__":
    print("Crypto Analytics Pipeline Started")
    print("Collection interval: 5 minutes")
    print("Test cycles:", MAX_CYCLES)

    try:
        for cycle in range(1, MAX_CYCLES + 1):
            cycle_start = time.monotonic()

            print(f"\nStarting Cycle {cycle} of {MAX_CYCLES}")
            run_pipeline()

            if cycle < MAX_CYCLES:
                elapsed = time.monotonic() - cycle_start
                wait_time = max(0, INTERVAL_SECONDS - elapsed)

                print(f"Next collection in {wait_time:.0f} seconds.")
                time.sleep(wait_time)

        print("\nTwo collection cycles completed.")

    except KeyboardInterrupt:
        print("\nPipeline stopped by user.")

    finally:
        engine.dispose()
        print("Database connection resources released.")
