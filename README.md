# Real-Time Crypto Analytics Pipeline

An end-to-end analytics project that collects cryptocurrency market data from CoinGecko, stores timestamped observations in Microsoft SQL Server, processes the data with Python and pandas, and will ultimately present insights in Power BI.

> **Project status:** In progress — Day 3 completed. Data quality checks, pandas cleaning, SQL Server integration, and a two-cycle automated pipeline test have been completed.

## Technology stack

- Python 3.11
- Requests
- pandas and NumPy
- SQL Server Express
- SQLAlchemy and pyodbc
- CoinGecko simple-price API
- Power BI (planned)
- Git and GitHub

## Current progress

### Day 1 — API extraction and pandas inspection

- Set up a Python virtual environment and installed dependencies.
- Connected to the CoinGecko simple-price endpoint.
- Retrieved Bitcoin and Ethereum prices in USD and their 24-hour percentage changes.
- Parsed the JSON response into a pandas DataFrame.
- Added a UTC collection timestamp and inspected the data using pandas methods.

### Day 2 — Multi-asset extraction, SQL Server storage, and automation

- Expanded extraction to five assets: Bitcoin, Ethereum, BNB, Solana, and XRP.
- Added a 15-second request timeout, exception handling, and up to three request attempts with exponential backoff.
- Created the `CryptoAnalyticsDB` database in SQL Server Express.
- Created `dbo.CryptoPriceHistory` to preserve historical snapshots. The table stores a unique ID, coin ID, USD price, 24-hour percentage change, collection timestamp, and database insertion timestamp.
- Connected Python to SQL Server using SQLAlchemy and ODBC Driver 18 with Windows authentication.
- Inserted API observations into SQL Server using pandas `to_sql(..., if_exists="append")`.
- Built a two-cycle automation test with a five-minute interval.

### Day 3 — Data quality, cleaning, and integrated pipeline

- Created `data_quality.py` to inspect DataFrame shape, columns, data types, missing values, duplicate rows, statistical summaries, and invalid prices.
- Created a reusable `clean_data.py` function that works on a copy of the input DataFrame.
- Standardized coin IDs by trimming whitespace and converting names to lowercase.
- Converted price and 24-hour change columns to numeric values and parsed timestamps as UTC.
- Removed rows missing essential fields (`coin`, `price`, or `timestamp`), empty coin IDs, and zero or negative prices.
- Removed duplicate observations using the combination of `coin` and `timestamp`, keeping the last record for a duplicate key.
- Kept missing `chg_24h` values because that field is optional; a missing percentage change should not discard an otherwise valid price observation.
- Tested the cleaning function on 10,000 synthetic rows: 9,998 remained after one invalid price and one duplicate observation were removed. The measured cleaning time in the local test was approximately 0.034 seconds (machine- and run-specific).
- Tested missing prices and invalid timestamps: two invalid rows were removed, while a valid XRP row with a missing `chg_24h` value was retained.
- Integrated cleaning into both `save_to_database.py` and `pipeline.py`, so data is cleaned before insertion into SQL Server.
- Verified the automated two-cycle run in SQL Server. The history table contained 8 records per asset (40 total) after the run.

**Automation scope:** The committed `pipeline.py` is configured for a two-cycle test (`MAX_CYCLES = 2`) with a five-minute interval between cycle starts. It is not an always-on background service.

## Data schema

The extraction and cleaned DataFrame contains one row per cryptocurrency snapshot:

| Column | Description |
| --- | --- |
| `coin` | CoinGecko cryptocurrency ID |
| `price` | Latest price in USD |
| `chg_24h` | 24-hour price change percentage; nullable |
| `timestamp` | UTC time when Python collected the response |

SQL Server table: `dbo.CryptoPriceHistory`

| Column | Description |
| --- | --- |
| `id` | Identity primary key |
| `coin` | Cryptocurrency ID |
| `price` | USD price (`DECIMAL(18,8)`) |
| `chg_24h` | 24-hour change (`DECIMAL(12,6)`) |
| `timestamp` | Collection timestamp stored as UTC in `DATETIME2(3)` |
| `created_at` | SQL Server insertion timestamp (UTC default) |

## Project structure

```text
realtime-crypto-analytics/
├── clean_data.py
├── data_quality.py
├── fetch.py
├── db_connection.py
├── save_to_database.py
├── pipeline.py
├── test_environment.py
├── requirements.txt
├── .gitignore
└── README.md
```

Runtime artifacts such as `pipeline.log` and the local `venv/` directory are excluded by `.gitignore`.

## Run locally

1. Clone this repository.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Ensure SQL Server Express is running and create the database/table using the schema described above.
5. Update the server name in `db_connection.py` to match your local SQL Server instance.
6. Test API extraction:

   ```bash
   python fetch.py
   ```

7. Inspect the fetched data:

   ```bash
   python data_quality.py
   ```

8. Run the synthetic cleaning tests (10,000-row test and edge-case test):

   ```bash
   python clean_data.py
   ```

9. Test the database connection:

   ```bash
   python db_connection.py
   ```

10. Fetch, clean, and insert one snapshot:

   ```bash
   python save_to_database.py
   ```

11. Run the two-cycle, five-minute automated pipeline test:

   ```bash
   python pipeline.py
   ```

The API is live, so prices and percentage changes vary. CoinGecko API availability and rate limits apply. The SQL Server connection configuration currently uses Windows authentication and ODBC Driver 18; adapt it for your own machine.

## Planned milestones

- [x] Fetch multiple cryptocurrencies from CoinGecko.
- [x] Add request timeout, exception handling, and retry logic.
- [x] Create SQL Server database and historical table.
- [x] Connect Python to SQL Server and insert observations.
- [x] Test scheduled five-minute collection for two cycles.
- [x] Inspect data quality and build a reusable pandas cleaning function.
- [x] Test cleaning on 10,000 synthetic rows and edge cases.
- [x] Integrate cleaning into manual and automated SQL Server insertion.
- [ ] Analyze returns, moving averages, volatility, and anomalies.
- [ ] Build an interactive Power BI dashboard.
- [ ] Improve long-running automation, monitoring, and deployment documentation.

## Notes

- Do not commit virtual environments, logs, local database files, API keys, or credentials.
- This is a near-real-time polling project, not a live exchange streaming feed.
- The five-minute polling interval is a project setting and should be adjusted to API limits and reliability needs.
- Duplicate observations are identified by the combination of cryptocurrency ID and collection timestamp. Historical records at different timestamps are preserved.
- No trading or investment recommendations are produced by this project.
