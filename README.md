# Real-Time Crypto Analytics Pipeline

An end-to-end analytics project that collects cryptocurrency market data from CoinGecko, stores timestamped observations in Microsoft SQL Server, processes the data with Python and pandas, and presents market and data-collection insights in a Power BI Desktop dashboard.

> **Project status:** Core pipeline, SQL analysis, and Power BI dashboard are built. Final documentation, longer-term data collection, and deployment improvements remain.

## Project overview

The project tracks five cryptocurrencies — Bitcoin, Ethereum, BNB, Solana, and XRP — using CoinGecko's simple-price API. Python fetches and validates the API response, pandas cleans the observations, SQL Server stores historical snapshots, and Power BI provides exploratory analysis.

This is a **near-real-time polling pipeline**, not a live exchange streaming feed.

## Technology stack

- Python 3.11
- Requests and pandas
- SQL Server Express
- SQLAlchemy and pyodbc
- CoinGecko simple-price API
- Power BI Desktop
- Git and GitHub

## Architecture

1. **Extract:** Request USD prices and API-reported 24-hour percentage changes for five assets.
2. **Validate and clean:** Handle malformed or partial responses, convert values, remove invalid prices and duplicate coin/timestamp observations, and retain valid records with a missing optional 24-hour change.
3. **Store:** Append timestamped observations to `dbo.CryptoPriceHistory` in SQL Server.
4. **Analyze:** Use SQL window functions, aggregation, interval-quality classification, and hourly price movement.
5. **Visualize:** Use Power BI Desktop for price trends, returns, volatility, anomaly exploration, and collection-interval quality.

## Repository structure

```text
realtime-crypto-analytics/
├── clean_data.py
├── fetch.py
├── db_connection.py
├── save_to_database.py
├── pipeline.py
├── test_environment.py
├── requirements.txt
├── .gitignore
├── README.md
└── sql/
    ├── day_07_crypto_analysis.sql
    └── day_08_hourly_analysis.sql
```

The Power BI report (`Crypto_Market_Analytics.pbix`) is maintained locally and is not included in this repository. Runtime artifacts such as the virtual environment, logs, local database files, and credentials should not be committed.

## Data model

### Source table: `dbo.CryptoPriceHistory`

| Column | Description |
| --- | --- |
| `id` | Identity primary key |
| `coin` | CoinGecko cryptocurrency ID |
| `price` | USD price (`DECIMAL(18,8)`) |
| `chg_24h` | API-reported 24-hour change (`DECIMAL(12,6)`, nullable) |
| `timestamp` | Python collection timestamp stored as UTC in `DATETIME2(3)` |
| `created_at` | SQL Server insertion timestamp, UTC default |

### Analytical views

- `dbo.vw_CryptoAnalytics` — existing snapshot-level market analysis and collection interval fields used by the Power BI report.
- `dbo.vw_CryptoIntervalQuality` — interval-quality analysis used to classify the time between consecutive observations.
- `dbo.vw_CryptoHourlyAnalysis` — hourly aggregation and price movement analysis created during Day 8. It includes hourly average, minimum, maximum, observation count, previous available hourly average, absolute price difference, and percentage change.

The reproducible Day 8 view definition is in [`sql/day_08_hourly_analysis.sql`](sql/day_08_hourly_analysis.sql). The Day 7 query exercises are in [`sql/day_07_crypto_analysis.sql`](sql/day_07_crypto_analysis.sql).

## Project progress

### Days 1–3 — Extraction, storage, cleaning, and pipeline integration

- Set up Python 3.11 and the project virtual environment.
- Connected to CoinGecko's simple-price endpoint and expanded from Bitcoin and Ethereum to five assets.
- Added request timeout, exception handling, retries with exponential backoff, response validation, and partial-response handling.
- Created `CryptoAnalyticsDB` and `dbo.CryptoPriceHistory` in SQL Server Express.
- Connected Python to SQL Server using SQLAlchemy, pyodbc, ODBC Driver 18, and Windows authentication.
- Built reusable pandas cleaning logic for coin IDs, numeric values, UTC timestamps, missing essential fields, invalid prices, and duplicate observations.
- Tested cleaning on 10,000 synthetic rows; 9,998 remained after one invalid-price row and one duplicate were removed. The measured runtime was approximately 0.034 seconds in that local test and is machine/run specific.
- Integrated cleaning into the manual save and pipeline workflows.

### Day 4 — SQL exploratory analysis and initial Power BI dashboard

- Used `LAG()` to calculate consecutive-snapshot returns, plus rolling averages, sample standard deviation, Z-scores, and exploratory anomaly flags.
- Created `vw_CryptoAnalytics` for Power BI.
- Built a local Power BI report with KPI cards, a cryptocurrency slicer, price and return visuals, volatility comparison, and an anomaly table.
- Confirmed that slicer selections filter relevant visuals.

**Interpretation limit:** Snapshot-to-snapshot returns are not the same as the API's 24-hour change. Early history was limited and contained collection gaps, so volatility and anomaly flags are exploratory rather than robust risk estimates or confirmed market anomalies.

### Day 5 — Pipeline reliability

- Distinguished permanent HTTP errors from retryable timeouts, connection failures, rate limits, and server errors.
- Tested empty API responses and simulated database insertion failure.
- Added pipeline logging and stage-level exception handling.
- Completed a successful two-cycle integration test, inserting five asset records per cycle. At that validation point, the table contained 14 records per cryptocurrency (70 total).

**Automation limitation:** The committed `pipeline.py` is configured with `MAX_CYCLES = 2` and a five-minute interval between cycle starts. It is a controlled two-cycle run, not an always-on background service.

### Day 6 — Collection interval quality

- Classified intervals between consecutive observations as `First Observation`, `Reliable Interval`, `Short Interval`, or `Long Interval`.
- Added interval fields to the SQL analytics model and created a Power BI collection-quality visual.
- Created a Reliable Collection Rate measure that excludes first observations from the denominator.
- Validated manual Power BI Desktop refresh and slicer interactions.

**Interpretation limit:** Reliable Collection Rate measures the share of comparable stored intervals classified as reliable under the project's interval thresholds. It is not API uptime, completeness across every possible period, or market performance. The current dashboard measure is dynamic; historical percentages documented in earlier development notes should not be treated as the current value.

### Day 7 — SQL analytical queries

Added six reproducible SQL exercises in `sql/day_07_crypto_analysis.sql`:

- Latest recorded price per cryptocurrency using a CTE and `ROW_NUMBER()`.
- Snapshot-to-snapshot returns using `LAG()` and `NULLIF()`.
- Five- and ten-observation moving averages.
- Highest and lowest recorded prices per cryptocurrency.
- Ranking by the latest API-reported 24-hour change.
- Average snapshot return and sample return volatility using SQL Server's `STDEV()`.

These scripts should be run against the target database to reproduce the results. Snapshot returns and API-reported 24-hour changes are kept distinct.

### Day 8 — Hourly market analysis and Power BI integration

- Aggregated observations into hourly buckets for each cryptocurrency.
- Calculated hourly average, minimum, maximum, and record count.
- Used `LAG()` to compare each hourly average with the previous available hourly bucket.
- Calculated absolute and percentage price movement.
- Created `dbo.vw_CryptoHourlyAnalysis` and verified it in SQL Server; the initial Power BI load returned 50 rows at the time of validation.
- Loaded the hourly analysis view into the existing Power BI report and added hourly price and percentage-movement analysis visuals.
- Updated the Reliable Collection Rate KPI to use the model's interval-quality data.

**Hourly interpretation limit:** Because collection intervals contain gaps, `LAG()` compares with the previous available hourly group for that cryptocurrency. This is not necessarily a one-clock-hour return. The hourly aggregates summarize only observations actually collected.

## Run locally

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Ensure SQL Server Express is running. Create `CryptoAnalyticsDB` and the `dbo.CryptoPriceHistory` table using the schema above.
5. Update the SQL Server instance configuration in `db_connection.py` for your machine. Do not commit credentials or secrets.
6. Test API extraction:

   ```bash
   python fetch.py
   ```

7. Run the cleaning tests:

   ```bash
   python clean_data.py
   ```

8. Test the database connection:

   ```bash
   python db_connection.py
   ```

9. Fetch, clean, and insert one snapshot:

   ```bash
   python save_to_database.py
   ```

10. Run the controlled two-cycle pipeline:

    ```bash
    python pipeline.py
    ```

11. In SQL Server Management Studio, run the scripts in the `sql/` folder against `CryptoAnalyticsDB`. The Day 8 script creates or alters `dbo.vw_CryptoHourlyAnalysis`.

12. Open the local Power BI report and connect it to the SQL Server database. Refresh the model after new records are inserted.

CoinGecko API availability and rate limits apply. Prices and percentage changes vary over time. Power BI Desktop refresh in this project is manual; scheduled refresh and unattended deployment have not been established.

## Current limitations and next improvements

- Collection history contains gaps; hourly analysis is based only on available observations.
- The committed pipeline is a finite two-cycle test, not a continuously running service.
- Power BI is a local Desktop report; no published dashboard or scheduled refresh is claimed.
- Volatility and anomaly analysis are exploratory and should be interpreted cautiously with the available history.
- Continue collecting data over a longer period and investigate synchronized return spikes.
- Add automated orchestration, monitoring, and deployment only after the local pipeline is stable and its operational requirements are defined.

## Project checklist

- [x] CoinGecko extraction for five cryptocurrencies.
- [x] Request timeout, retry logic, and response validation.
- [x] SQL Server historical storage.
- [x] Python cleaning and validation.
- [x] Controlled pipeline reliability tests.
- [x] SQL snapshot analysis and interval-quality analysis.
- [x] Power BI Desktop dashboard and manual refresh validation.
- [x] Day 7 reusable SQL analysis script.
- [x] Day 8 hourly analysis view and Power BI integration.
- [ ] Add selected dashboard screenshots to the repository.
- [ ] Collect a longer, more continuous history and reassess analytical stability.
- [ ] Implement and document unattended orchestration and deployment.

## Notes

- Never commit virtual environments, logs, local database files, API keys, or credentials.
- This project is for analytics and learning; it does not generate trading or investment recommendations.
