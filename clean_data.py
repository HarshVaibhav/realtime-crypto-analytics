"""Data cleaning and validation for cryptocurrency snapshots."""

import time

import numpy as np
import pandas as pd

from fetch import fetch

REQUIRED_COLUMNS = {"coin", "price", "chg_24h", "timestamp"}


def clean_data(dataframe):
    """Return a cleaned copy of a snapshot DataFrame.

    Essential fields are coin, price, and timestamp. The API's 24-hour
    change is optional; invalid or infinite values are converted to missing.
    """
    if dataframe is None:
        raise ValueError("Input dataframe cannot be None.")

    missing_columns = REQUIRED_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(
            "Input dataframe is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    dataframe = dataframe.copy()
    original_rows = len(dataframe)

    dataframe["coin"] = (
        dataframe["coin"].astype("string").str.strip().str.lower()
    )
    dataframe["price"] = pd.to_numeric(dataframe["price"], errors="coerce")
    dataframe["chg_24h"] = pd.to_numeric(dataframe["chg_24h"], errors="coerce")
    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"], errors="coerce", utc=True
    )

    # Infinity is numeric to pandas but cannot be stored safely in DECIMAL.
    dataframe.loc[~np.isfinite(dataframe["price"]), "price"] = np.nan
    dataframe.loc[~np.isfinite(dataframe["chg_24h"]), "chg_24h"] = np.nan

    dataframe = dataframe.dropna(subset=["coin", "price", "timestamp"])
    dataframe = dataframe[dataframe["coin"].str.len() > 0]
    dataframe = dataframe[dataframe["price"] > 0]
    dataframe = dataframe.drop_duplicates(
        subset=["coin", "timestamp"], keep="last"
    ).reset_index(drop=True)

    print("\n--- CLEANING SUMMARY ---")
    print("Original rows:", original_rows)
    print("Cleaned rows:", len(dataframe))
    print("Rows removed:", original_rows - len(dataframe))
    return dataframe


def test_live_data():
    """Fetch and clean one live CoinGecko response."""
    print("\n--- LIVE API DATA TEST ---")
    dataframe = fetch()
    if dataframe is None or dataframe.empty:
        print("No data available.")
        return
    print(clean_data(dataframe).to_string(index=False))


def test_large_dataset():
    """Exercise cleaning behaviour and runtime on synthetic records."""
    print("\n--- GENERATING 10,000 TEST RECORDS ---")
    coins = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]
    test_data = pd.DataFrame({
        "coin": [coins[i % 5] for i in range(10000)],
        "price": np.random.uniform(1, 80000, 10000),
        "chg_24h": np.random.uniform(-10, 10, 10000),
        "timestamp": pd.date_range(
            start="2026-11-01", periods=10000, freq="min", tz="UTC"
        ),
    })
    test_data.loc[10, "price"] = -10
    test_data.loc[9999] = test_data.loc[0]

    start_time = time.perf_counter()
    cleaned_data = clean_data(test_data)
    elapsed = time.perf_counter() - start_time

    print("\n--- PERFORMANCE RESULTS ---")
    print("Cleaning time:", round(elapsed, 4), "seconds")
    print("Final row count:", len(cleaned_data))
    print(
        "Remaining duplicates:",
        cleaned_data.duplicated(subset=["coin", "timestamp"]).sum(),
    )


def test_edge_cases():
    """Exercise missing values, invalid timestamps, and infinite values."""
    test_data = pd.DataFrame({
        "coin": ["bitcoin", "ethereum", "solana", "ripple", "bnb"],
        "price": [80000, np.nan, 100, 1.5, np.inf],
        "chg_24h": [2.5, 3.0, 4.0, np.nan, np.inf],
        "timestamp": [
            "2026-11-05 08:00:00",
            "2026-11-05 08:01:00",
            "invalid-date",
            "2026-11-05 08:03:00",
            "2026-11-05 08:04:00",
        ],
    })
    cleaned_data = clean_data(test_data)
    assert len(cleaned_data) == 1
    assert pd.isna(cleaned_data.loc[0, "chg_24h"])
    print("Edge-case checks passed.")


if __name__ == "__main__":
    test_large_dataset()
    test_edge_cases()
    # Uncomment to test live API data separately:
    # test_live_data()
