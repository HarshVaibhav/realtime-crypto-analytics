"""Fetch cryptocurrency prices from CoinGecko with basic retry handling."""

import time

import pandas as pd
import requests

# CoinGecko simple-price endpoint.
URL = "https://api.coingecko.com/api/v3/simple/price"

# Five assets priced in USD, including their 24-hour percentage change.
params = {
    "ids": "bitcoin,ethereum,binancecoin,solana,ripple",
    "vs_currencies": "usd",
    "include_24hr_change": "true",
}

MAX_RETRIES = 3


def fetch():
    """Fetch current prices and return one row per cryptocurrency."""
    response = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"API Request: Attempt {attempt}")

            response = requests.get(
                URL,
                params=params,
                timeout=15,
            )
            response.raise_for_status()

            print("Status Code:", response.status_code)
            break

        except requests.exceptions.RequestException as error:
            print("Request failed:", error)

            if attempt == MAX_RETRIES:
                print("Maximum retries reached.")
                return None

            wait_time = 2 ** (attempt - 1)
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    try:
        data = response.json()
        rows = []

        for coin, values in data.items():
            rows.append(
                {
                    "coin": coin,
                    "price": values["usd"],
                    "chg_24h": values["usd_24h_change"],
                }
            )

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.Timestamp.now(tz="UTC")
        return df

    except (ValueError, KeyError, TypeError) as error:
        print("Data Processing Error:", error)
        return None


if __name__ == "__main__":
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
