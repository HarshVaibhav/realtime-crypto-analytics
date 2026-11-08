# Real-Time Crypto Analytics Pipeline

An end-to-end analytics project that collects cryptocurrency market data from CoinGecko, stores timestamped observations in Microsoft SQL Server, processes the data with Python and pandas, and presents exploratory and data-quality insights in a Power BI Desktop dashboard.

> **Project status:** In progress — Day 6 completed. API extraction, cleaning, SQL storage, analytical views, Power BI visuals, interval-quality analysis, and controlled pipeline reliability tests are complete. Dashboard refinement, reproducible SQL documentation, longer-term collection, and deployment remain.

## Technology stack

- Python 3.11
- Requests
- pandas and NumPy
- SQL Server Express
- SQLAlchemy and pyodbc
- CoinGecko simple-price API
- Power BI Desktop
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

### Day 4 — SQL exploratory analysis and initial Power BI dashboard

- Analyzed the 40 stored snapshots (8 per cryptocurrency) in SQL Server.
- Calculated consecutive-observation percentage returns with `LAG(price)` partitioned by cryptocurrency. These are **snapshot-to-snapshot returns**, not CoinGecko's API-provided 24-hour change.
- Calculated a rolling three-observation price average using SQL window functions.
- Calculated per-asset average snapshot returns and sample standard deviation of returns as an exploratory volatility measure.
- Computed Z-scores and flagged potential anomalies using an exploratory threshold; the first observation per asset has no previous price and therefore no snapshot return.
- Prepared a SQL analytics view named `vw_CryptoAnalytics` for Power BI consumption.
- Connected Power BI Desktop to the analytics view and built an initial local report named `Crypto_Market_Analytics`.
- Added KPI cards for distinct tracked cryptocurrencies, latest price, average volatility, and average API-reported 24-hour change.
- Added a cryptocurrency slicer, snapshot-return comparison chart, price chart, volatility-by-asset bar chart, and potential-anomalies table.
- Verified the slicer changes KPI values when an individual cryptocurrency is selected.
- Improved the snapshot-return chart by using a categorical timestamp axis and removed the duplicate chart.

**Interpretation limits:** The initial dataset had only eight observations per asset, collected across two days with a substantial gap. The resulting volatility and Z-scores are descriptive demonstrations, **not robust estimates of market risk**. All five assets showed flagged movements at approximately the same collection time; this may reflect actual market movement or a collection/data issue and requires investigation. Do not interpret these flags as confirmed market anomalies.

### Day 5 — Pipeline reliability and error handling

- Improved CoinGecko request handling to distinguish permanent HTTP errors (such as 404) from retryable conditions (such as timeouts, connection errors, HTTP 429, and server-side 5xx responses).
- Added validation for empty or invalid API payloads and partial coin responses. Invalid individual records are skipped rather than causing the entire response to fail.
- Tested the empty-response path by substituting an empty dictionary after a successful API request. The fetch function returned `None` and did not pass an empty DataFrame downstream.
- Added exception handling around the pipeline stages and SQL insertion, with detailed error tracebacks written to `pipeline.log`.
- Simulated a database failure deliberately and verified that the exception was caught, both collection cycles completed, and the process exited cleanly with 2 failed cycles rather than an unhandled crash.
- Disabled the test switches and ran the real two-cycle pipeline successfully: 5 records fetched, cleaned, and inserted per cycle; 2 successful cycles and 0 failed cycles.
- Verified the SQL Server history table in SSMS after the successful run: **14 records per cryptocurrency, 70 records total** across the five tracked assets.
- Added a table-existence check before insertion in the pipeline to avoid accidentally creating a new table when the intended SQL table is missing.

**Reliability test scope:** These are controlled failure simulations and a successful two-cycle integration test. They demonstrate the tested exception-handling paths, but do not constitute a long-duration production uptime test or prove recovery from every possible real SQL Server outage.

**Automation scope:** The committed `pipeline.py` is configured for a two-cycle test (`MAX_CYCLES = 2`) with a five-minute interval between cycle starts. It is not an always-on background service.

### Day 6 — Collection interval quality and Power BI refresh validation

- Added SQL interval analysis to distinguish `First Observation`, `Reliable Interval`, `Short Interval`, and `Long Interval` records using the time difference between consecutive observations for each cryptocurrency.
- The Power BI model now includes the interval fields `previous_timestamp`, `interval_seconds`, `interval_status`, and `reliable_return_pct` alongside the existing market-analysis fields.
- Built a stacked column chart, **Data Collection Interval Quality**, to compare interval categories by cryptocurrency.
- Created a DAX measure, **Reliable Collection Rate**, that excludes first observations because they have no preceding timestamp and calculates reliable intervals as a share of all comparable intervals:

  ```DAX
  Reliable Collection Rate =
  VAR ReliableCount =
      CALCULATE(
          COUNTROWS('vw_CryptoAnalytics'),
          'vw_CryptoAnalytics'[interval_status] = "Reliable Interval"
      )
  VAR ValidIntervals =
      CALCULATE(
          COUNTROWS('vw_CryptoAnalytics'),
          'vw_CryptoAnalytics'[interval_status] <> "First Observation"
      )
  RETURN
      DIVIDE(ReliableCount, ValidIntervals, 0)
  ```

- Validated the measure against the observed interval counts per asset: 15 reliable intervals out of 25 comparable intervals, producing **60.00%**. The first observation is excluded from the denominator.
- Tested the cryptocurrency slicer against the interval chart and potential-anomalies table. The selected asset filters those visuals; clearing the selection restores all five assets.
- Verified new SQL records for all five cryptocurrencies at `2026-11-08 16:07:10.916`, with the preceding batch at `2026-11-08 16:02:10.906`.
- Refreshed the Power BI Desktop model and confirmed that the updated report displays the collection-quality visual, anomaly table, slicer, and reliable collection KPI.

**Refresh limitation:** This validates a **manual Power BI Desktop refresh** after new SQL rows were inserted. It does not establish automatic scheduled refresh or live streaming. The Python pipeline remains a finite two-cycle test rather than an always-on service.

**Interval interpretation:** The 60% result is based on the current stored history and the interval classification logic. It is a collection-cadence metric, not API uptime, data completeness over all possible periods, or market performance. The interval thresholds should be documented alongside the SQL definition before the metric is treated as a production service-level indicator.

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
├── data_quality.py  # local script; repository presence not verified
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
- [x] Analyze returns, moving averages, volatility, and exploratory anomaly flags.
- [x] Build the initial interactive Power BI dashboard locally.
- [x] Test empty API responses and simulated database failures.
- [x] Verify successful two-cycle pipeline execution and SQL record counts.
- [x] Build collection interval quality analysis and a reliable collection KPI.
- [x] Validate cryptocurrency slicer interactions and manual Power BI refresh.
- [ ] Upload reproducible SQL analytics and interval-quality view-definition scripts.
- [ ] Upload a shareable dashboard artifact or selected screenshots.
- [ ] Investigate synchronized return spikes and collect a longer, more continuous history.
- [ ] Improve long-running automation, monitoring, and deployment documentation.

## Notes

- Do not commit virtual environments, logs, local database files, API keys, or credentials.
- This is a near-real-time polling project, not a live exchange streaming feed.
- The five-minute polling interval is a project setting and should be adjusted to API limits and reliability needs.
- Duplicate observations are identified by the combination of cryptocurrency ID and collection timestamp. Historical records at different timestamps are preserved.
- No trading or investment recommendations are produced by this project.
