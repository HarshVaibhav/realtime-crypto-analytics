"""
Fetch cryptocurrency prices from CoinGecko.

Features:
- HTTP error handling
- Retry mechanism
- Exponential backoff
- Request timeout
- API response validation
- Partial data handling
- UTC timestamps
- Optional empty-response test mode
"""

import logging
import time

import pandas as pd
import requests

URL = "https://api.coingecko.com/api/v3/simple/price"

PARAMS = {
    "ids": "bitcoin,ethereum,binancecoin,solana,ripple",
    "vs_currencies": "usd",
    "include_24hr_change": "true",
}

MAX_RETRIES = 3
REQUEST_TIMEOUT = 15

# Keep False for normal live API collection.
# Set True only when testing the empty-response handling.
TEST_EMPTY_RESPONSE = False

logger = logging.getLogger(__name__)


def fetch():
    """Fetch cryptocurrency data and return a DataFrame."""

    data = None

    # Request data with retry handling.
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"\nAPI Request: Attempt {attempt}")

            response = requests.get(
                URL,
                params=PARAMS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            print("Status Code:", response.status_code)
            data = response.json()
            break

        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code

            logger.error("HTTP error: %s", error)
            print("HTTP Error:", status_code)

            # Retry rate limits and server errors, not permanent 4xx errors.
            if status_code != 429 and status_code < 500:
                print("Permanent HTTP error. Stopping retries.")
                return None

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as error:
            logger.warning("Temporary API connection failure: %s", error)
            print("Connection or timeout error:", error)

        except requests.exceptions.RequestException as error:
            logger.exception("Unexpected request error: %s", error)
            print("Request failed:", error)
            return None

        except ValueError as error:
            logger.exception("Invalid JSON response: %s", error)
            print("API returned invalid JSON.")
            return None

        if attempt < MAX_RETRIES:
            wait_time = 2 ** (attempt - 1)
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            logger.error("Maximum API retries reached.")
            print("Maximum retries reached.")
            return None

    # Optional test hook: replace a successful response with an empty payload.
    if TEST_EMPTY_RESPONSE:
        print("\nTEST MODE: Simulating an empty API response.")
        data = {}

    # Validate the overall response.
    if not isinstance(data, dict) or not data:
        logger.error("API returned empty or invalid data.")
        print("No valid API data received.")
        return None

    # Extract valid records; skip malformed individual coin entries.
    rows = []

    for coin, values in data.items():
        if not isinstance(values, dict):
            logger.warning("Invalid response for %s. Skipping.", coin)
            continue

        price = values.get("usd")

        if price is None:
            logger.warning("Missing USD price for %s. Skipping.", coin)
            continue

        try:
            price = float(price)
            if price <= 0:
                logger.warning("Invalid price for %s. Skipping.", coin)
                continue
        except (ValueError, TypeError):
            logger.warning("Non-numeric price for %s. Skipping.", coin)
            continue

        change = values.get("usd_24h_change")

        try:
            change = float(change) if change is not None else None
        except (ValueError, TypeError):
            change = None

        rows.append(
            {
                "coin": coin,
                "price": price,
                "chg_24h": change,
            }
        )

    if not rows:
        logger.error("No valid cryptocurrency records found.")
        print("No valid records available.")
        return None

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.Timestamp.now(tz="UTC")

    logger.info(
        "Successfully fetched %s cryptocurrency records.",
        len(df),
    )
    print("\nSuccessfully fetched records:", len(df))

    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    crypto_df = fetch()

    if crypto_df is not None:
        print("\nExtracted Cryptocurrency Data:")
        print(crypto_df)

        print("\nDataFrame Information:")
        crypto_df.info()

        print("\nFirst 5 Records:")
        print(crypto_df.head())

        print("\nDataFrame Shape:")
        print(crypto_df.shape)

        print("\nColumn Names:")
        print(crypto_df.columns)

        print("\nData Types:")
        print(crypto_df.dtypes)

        print("\nStatistical Summary:")
        print(crypto_df.describe())
    else:
        print("\nData extraction failed.")
