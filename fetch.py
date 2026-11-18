"""
Fetch cryptocurrency prices from CoinGecko.

Features:
- HTTP error handling
- Retry mechanism with exponential backoff
- Request timeout and response validation
- Partial data handling
- Finite, positive USD price validation
- UTC timestamps
- Optional empty-response test mode
"""

import logging
import math
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
    """Fetch cryptocurrency data and return a validated DataFrame."""
    data = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("CoinGecko request attempt %s/%s", attempt, MAX_RETRIES)
            response = requests.get(URL, params=PARAMS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            break

        except requests.exceptions.HTTPError as error:
            status_code = error.response.status_code
            logger.error("CoinGecko HTTP error: %s", error)

            # Retry rate limits and server errors, not permanent client errors.
            if status_code != 429 and status_code < 500:
                logger.error("Permanent HTTP error; stopping retries.")
                return None

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as error:
            logger.warning("Temporary API connection failure: %s", error)

        except requests.exceptions.RequestException:
            logger.exception("Unexpected request error.")
            return None

        except ValueError:
            logger.exception("CoinGecko returned invalid JSON.")
            return None

        if attempt < MAX_RETRIES:
            wait_time = 2 ** (attempt - 1)
            logger.info("Retrying in %s seconds.", wait_time)
            time.sleep(wait_time)
        else:
            logger.error("Maximum API retries reached.")
            return None

    if TEST_EMPTY_RESPONSE:
        logger.warning("TEST MODE: simulating an empty API response.")
        data = {}

    if not isinstance(data, dict) or not data:
        logger.error("API returned empty or invalid data.")
        return None

    rows = []
    for coin, values in data.items():
        if not isinstance(values, dict):
            logger.warning("Invalid response for %s; skipping.", coin)
            continue

        try:
            price = float(values.get("usd"))
        except (TypeError, ValueError):
            logger.warning("Missing or non-numeric USD price for %s; skipping.", coin)
            continue

        if not math.isfinite(price) or price <= 0:
            logger.warning("Non-finite or non-positive USD price for %s; skipping.", coin)
            continue

        try:
            change = float(values["usd_24h_change"])
            if not math.isfinite(change):
                change = None
        except (KeyError, TypeError, ValueError):
            change = None

        rows.append({"coin": coin, "price": price, "chg_24h": change})

    if not rows:
        logger.error("No valid cryptocurrency records found.")
        return None

    dataframe = pd.DataFrame(rows)
    dataframe["timestamp"] = pd.Timestamp.now(tz="UTC")

    logger.info("Successfully fetched %s cryptocurrency records.", len(dataframe))
    return dataframe


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    crypto_df = fetch()
    if crypto_df is None:
        print("Data extraction failed.")
    else:
        print(crypto_df.to_string(index=False))
        print("\nShape:", crypto_df.shape)
        print("\nData types:")
        print(crypto_df.dtypes)
