import pandas as pd
import numpy as np
import time

from fetch import fetch


# ==========================================
# 1. DATA CLEANING FUNCTION
# ==========================================

def clean_data(df):
    """Validate and clean a cryptocurrency snapshot DataFrame."""

    # Work on a copy; preserve the original DataFrame.
    df = df.copy()
    original_rows = len(df)

    print("\n--- CLEANING STARTED ---")
    print("Original rows:", original_rows)

    # Standardize cryptocurrency IDs.
    df["coin"] = (
        df["coin"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    # Convert numeric columns; invalid values become NaN.
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["chg_24h"] = pd.to_numeric(df["chg_24h"], errors="coerce")

    # Parse timestamps and normalize them to UTC.
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True,
    )

    # Remove rows missing essential fields.
    df = df.dropna(subset=["coin", "price", "timestamp"])

    # Remove empty cryptocurrency IDs.
    df = df[df["coin"].str.strip() != ""]

    # Remove zero or negative prices.
    df = df[df["price"] > 0]

    # Treat the same coin + timestamp as a duplicate observation.
    # Keep the last occurrence and preserve historical timestamps.
    df = df.drop_duplicates(
        subset=["coin", "timestamp"],
        keep="last",
    )

    df = df.reset_index(drop=True)

    cleaned_rows = len(df)

    print("\n--- CLEANING SUMMARY ---")
    print("Original rows:", original_rows)
    print("Cleaned rows:", cleaned_rows)
    print("Rows removed:", original_rows - cleaned_rows)

    return df


# ==========================================
# 2. LIVE API DATA TEST
# ==========================================

def test_live_data():
    """Fetch and clean one live CoinGecko response."""

    print("\n--- LIVE API DATA TEST ---")
    df = fetch()

    if df is None or df.empty:
        print("No data available.")
        return

    cleaned_df = clean_data(df)

    print("\n--- CLEANED LIVE DATA ---")
    print(cleaned_df)

    print("\n--- FINAL DATA TYPES ---")
    print(cleaned_df.dtypes)

    print("\n--- MISSING VALUES ---")
    print(cleaned_df.isnull().sum())


# ==========================================
# 3. GENERATE AND TEST 10,000 RECORDS
# ==========================================

def test_large_dataset():
    """Test cleaning behaviour and runtime on synthetic records."""

    print("\n--- GENERATING 10,000 TEST RECORDS ---")

    coins = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]

    test_data = pd.DataFrame({
        "coin": [coins[i % 5] for i in range(10000)],
        "price": np.random.uniform(1, 80000, 10000),
        "chg_24h": np.random.uniform(-10, 10, 10000),
        "timestamp": pd.date_range(
            start="2026-11-01",
            periods=10000,
            freq="min",
            tz="UTC",
        ),
    })

    # Introduce one invalid price and one exact duplicate row.
    test_data.loc[10, "price"] = -10
    test_data.loc[9999] = test_data.loc[0]

    print("Test dataset created.")
    print("Dataset shape:", test_data.shape)

    start_time = time.perf_counter()
    cleaned_data = clean_data(test_data)
    end_time = time.perf_counter()

    print("\n--- PERFORMANCE RESULTS ---")
    print("Cleaning time:", round(end_time - start_time, 4), "seconds")
    print("Final row count:", len(cleaned_data))
    print(
        "Remaining duplicates:",
        cleaned_data.duplicated(subset=["coin", "timestamp"]).sum(),
    )

    print("\n--- CLEANED DATA PREVIEW ---")
    print(cleaned_data.head())


# ==========================================
# 4. TEST MISSING VALUES AND INVALID TIMESTAMPS
# ==========================================

def test_edge_cases():
    """Verify essential-field removal and optional-field retention."""

    print("\n--- TESTING MISSING VALUES AND INVALID TIMESTAMPS ---")

    test_data = pd.DataFrame({
        "coin": ["bitcoin", "ethereum", "solana", "ripple"],
        "price": [80000, np.nan, 100, 1.5],
        "chg_24h": [2.5, 3.0, 4.0, np.nan],
        "timestamp": [
            "2026-11-05 08:00:00",
            "2026-11-05 08:01:00",
            "invalid-date",
            "2026-11-05 08:03:00",
        ],
    })

    print("\nOriginal test data:")
    print(test_data)

    cleaned_data = clean_data(test_data)

    print("\n--- EDGE CASE TEST RESULTS ---")
    print("Final records:", len(cleaned_data))

    print("\nCleaned data:")
    print(cleaned_data)

    print("\nMissing values after cleaning:")
    print(cleaned_data.isnull().sum())


# ==========================================
# 5. MAIN PROGRAM
# ==========================================

if __name__ == "__main__":
    # Run synthetic tests by default; these do not call the API or SQL Server.
    test_large_dataset()
    test_edge_cases()

    # To test live API data separately, uncomment:
    # test_live_data()
