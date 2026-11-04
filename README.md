# Real-Time Crypto Analytics Pipeline

An end-to-end analytics project that collects cryptocurrency market data from CoinGecko, stores timestamped observations in Microsoft SQL Server, processes the data with Python and pandas, and will ultimately present insights in Power BI.

> **Project status:** In progress — Day 2 completed. Automated collection has been tested for two cycles at a five-minute interval.

## Technology stack

- Python 3.11
- Requests
- pandas
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
- Verified four records per asset (20 total) in SQL Server after two earlier manual inserts and two automated collection cycles.

**Automation scope:** The committed `pipeline.py` is configured for a two-cycle test (`MAX_CYCLES = 2`). It is not configured as an always-on background service.

## Data schema

The extraction DataFrame contains one row per cryptocurrency:

| Column | Description |
| --- | --- |
| `coin` | CoinGecko cryptocurrency ID |
| `price` | Latest price in USD |
| `chg_24h` | 24-hour price change percentage |
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
6. Test the API extraction:

   ```bash
   python fetch.py
   ```

7. Test the database connection:

   ```bash
   python db_connection.py
   ```

8. Insert one snapshot for each configured asset:

   ```bash
   python save_to_database.py
   ```

9. Run the two-cycle, five-minute automation test:

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
- [ ] Add data quality checks and cleaning.
- [ ] Analyze returns, moving averages, volatility, and anomalies.
- [ ] Build an interactive Power BI dashboard.
- [ ] Improve long-running automation, monitoring, and deployment documentation.

## Notes

- Do not commit virtual environments, logs, local database files, API keys, or credentials.
- This is a near-real-time polling project, not a live exchange streaming feed.
- The five-minute polling interval is a project setting and should be adjusted to API limits and reliability needs.
- No trading or investment recommendations are produced by this project.
