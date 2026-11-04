"""Run a two-cycle test of the five-minute crypto data pipeline."""

import logging
import time

from fetch import fetch
from db_connection import engine

INTERVAL_SECONDS = 300
MAX_CYCLES = 2

logging.basicConfig(
    filename="pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run_pipeline():
    """Fetch one snapshot and append it to the SQL Server history table."""
    logging.info("Starting collection cycle.")

    crypto_df = fetch()

    if crypto_df is None or crypto_df.empty:
        logging.error("No data received. Cycle failed.")
        print("No cryptocurrency data available.")
        return False

    try:
        crypto_df["timestamp"] = (
            crypto_df["timestamp"]
            .dt.tz_convert("UTC")
            .dt.tz_localize(None)
        )

        with engine.begin() as connection:
            crypto_df.to_sql(
                name="CryptoPriceHistory",
                con=connection,
                schema="dbo",
                if_exists="append",
                index=False,
            )

        logging.info("Successfully inserted %s records.", len(crypto_df))
        print(f"Successfully inserted {len(crypto_df)} records.")
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
