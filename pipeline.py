"""
Real-Time Cryptocurrency Analytics Pipeline

Features:
- Fetch cryptocurrency data from CoinGecko
- Clean and validate data
- Store records in SQL Server
- Handle API and database errors
- Log pipeline execution
- Track successful and failed cycles
- Support controlled database-failure testing
"""

import logging
import time
from pathlib import Path

from fetch import fetch
from clean_data import clean_data
from db_connection import engine


# Configuration
INTERVAL_SECONDS = 300
MAX_CYCLES = 2

# False = normal SQL Server insertion.
# True = deliberately simulate a database failure.
TEST_DATABASE_FAILURE = False

TABLE_NAME = "CryptoPriceHistory"


# Log file is created beside this script.
logging.basicConfig(
    filename=str(Path(__file__).resolve().parent / "pipeline.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,
)

logger = logging.getLogger(__name__)


def run_pipeline():
    """Fetch, clean, and save one cryptocurrency snapshot."""

    logger.info("Starting collection cycle.")
    print("\n--- NEW COLLECTION CYCLE ---")

    try:
        # STEP 1: Fetch API data.
        print("\nStep 1: Fetching cryptocurrency data...")
        crypto_df = fetch()

        if crypto_df is None or crypto_df.empty:
            logger.error("API returned no usable data.")
            print("No cryptocurrency data available.")
            return False

        print("Records fetched:", len(crypto_df))

        # STEP 2: Clean and validate data.
        print("\nStep 2: Cleaning data...")
        cleaned_df = clean_data(crypto_df)

        if cleaned_df is None or cleaned_df.empty:
            logger.error("No valid records after cleaning.")
            print("No valid records. Database insertion skipped.")
            return False

        print("Valid records:", len(cleaned_df))

        # STEP 3: Convert timezone-aware UTC timestamps to UTC-naive
        # values because SQL Server DATETIME2 does not store a timezone.
        cleaned_df["timestamp"] = (
            cleaned_df["timestamp"]
            .dt.tz_convert("UTC")
            .dt.tz_localize(None)
        )

        # STEP 4: Insert records into SQL Server.
        print("\nStep 3: Saving data to SQL Server...")

        try:
            with engine.begin() as connection:
                if TEST_DATABASE_FAILURE:
                    print("TEST MODE: Simulating database failure.")
                    raise RuntimeError("Simulated database failure")

                # Check that the intended table exists. This prevents
                # pandas to_sql from creating a new table unintentionally.
                table_exists = connection.dialect.has_table(
                    connection,
                    TABLE_NAME,
                    schema="dbo",
                )

                if not table_exists:
                    raise RuntimeError(
                        f"Required table dbo.{TABLE_NAME} does not exist."
                    )

                cleaned_df.to_sql(
                    name=TABLE_NAME,
                    con=connection,
                    schema="dbo",
                    if_exists="append",
                    index=False,
                )

            logger.info(
                "Successfully inserted %s records.",
                len(cleaned_df),
            )
            print("Database insertion successful!")
            print("Records inserted:", len(cleaned_df))
            return True

        except Exception:
            logger.exception("Database insertion failed.")
            print("Database insertion failed.")
            print("Check pipeline.log for detailed error.")
            return False

    except Exception:
        logger.exception("Unexpected pipeline failure.")
        print("Unexpected pipeline error.")
        print("Check pipeline.log for details.")
        return False


if __name__ == "__main__":
    print("\nCrypto Analytics Pipeline Started")
    print("Executing file:", Path(__file__).resolve())
    print("Collection interval:", INTERVAL_SECONDS, "seconds")
    print("Maximum test cycles:", MAX_CYCLES)
    print(
        "Database failure simulation:",
        "ENABLED" if TEST_DATABASE_FAILURE else "DISABLED",
    )

    logger.info(
        "Pipeline started. Database failure simulation enabled: %s",
        TEST_DATABASE_FAILURE,
    )

    successful_cycles = 0
    failed_cycles = 0
    completed_cycles = 0

    try:
        for cycle in range(1, MAX_CYCLES + 1):
            cycle_start = time.monotonic()

            print(f"\nStarting Cycle {cycle} of {MAX_CYCLES}")
            success = run_pipeline()
            completed_cycles += 1

            if success:
                successful_cycles += 1
            else:
                failed_cycles += 1

            # Keep five minutes between cycle start times.
            if cycle < MAX_CYCLES:
                elapsed = time.monotonic() - cycle_start
                wait_time = max(0, INTERVAL_SECONDS - elapsed)

                print(f"\nNext collection in {wait_time:.0f} seconds.")
                time.sleep(wait_time)

        print("\n========== PIPELINE SUMMARY ==========")
        print("Total cycles:", completed_cycles)
        print("Successful cycles:", successful_cycles)
        print("Failed cycles:", failed_cycles)

        logger.info(
            "Pipeline completed. Total=%s, Success=%s, Failed=%s",
            completed_cycles,
            successful_cycles,
            failed_cycles,
        )

    except KeyboardInterrupt:
        print("\nPipeline stopped by user.")
        logger.warning("Pipeline manually interrupted.")

    finally:
        engine.dispose()
        print("\nDatabase connection resources released.")
        print("Pipeline execution finished.")
