"""Fetch current cryptocurrency prices from CoinGecko and inspect them."""

import requests
import pandas as pd

# CoinGecko simple-price endpoint.
URL = "https://api.coingecko.com/api/v3/simple/price"

# Request Bitcoin and Ethereum prices in USD, including 24-hour change.
PARAMS = {
    "ids": "bitcoin,ethereum",
    "vs_currencies": "usd",
    "include_24hr_change": "true",
}


def fetch() -> pd.DataFrame:
    """Fetch market data and return one row per cryptocurrency."""
    response = requests.get(URL, params=PARAMS, timeout=15)
    print("Status Code:", response.status_code)
    response.raise_for_status()

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


if __name__ == "__main__":
    crypto_df = fetch()

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
