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
import os
import time
from pathlib import Path

from fetch import fetch
from clean_data import clean_data
from db_connection import engine
from database_writer import insert_snapshot


# Configuration
INTERVAL_SECONDS = max(1, int(os.getenv("INTERVAL_SECONDS", "300")))
# 0 means run until interrupted; set MAX_CYCLES=2 for a short test.
MAX_CYCLES = max(0, int(os.getenv("MAX_CYCLES", "0")))

# False = normal SQL Server insertion.
# True = deliberately simulate a database failure.
TEST_DATABASE_FAILURE = False


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

                inserted, skipped = insert_snapshot(connection, cleaned_df)

            logger.info(
                "Inserted %s records; skipped %s existing observations.",
                inserted,
                skipped,
            )
            print("Database insertion successful!")
            print("New records inserted:", inserted)
            print("Existing observations skipped:", skipped)
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
    print("Maximum cycles:", MAX_CYCLES if MAX_CYCLES else "unlimited (Ctrl+C to stop)")
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
        cycle = 0
        while MAX_CYCLES == 0 or cycle < MAX_CYCLES:
            cycle += 1
            cycle_start = time.monotonic()

            print(f"\nStarting Cycle {cycle} of {MAX_CYCLES}")
            success = run_pipeline()
            completed_cycles += 1

            if success:
                successful_cycles += 1
            else:
                failed_cycles += 1

            # Keep five minutes between cycle start times.
            if MAX_CYCLES == 0 or cycle < MAX_CYCLES:
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
