# Real-Time Crypto Analytics Pipeline

An end-to-end analytics project that collects cryptocurrency market data from a public API, stores historical observations in SQL Server, transforms and analyzes the data with Python and pandas, and presents insights in Power BI.

> **Project status:** In progress — Day 1 completed.

## Technology stack

- Python 3.11
- Requests
- pandas
- SQL Server
- SQLAlchemy and pyodbc
- Power BI
- Git and GitHub

## Current progress

### Day 1 — API data extraction and pandas inspection

- Set up a Python virtual environment.
- Installed the project dependencies.
- Connected to the CoinGecko simple-price API.
- Retrieved Bitcoin and Ethereum prices in USD and their 24-hour percentage changes.
- Parsed the JSON response into Python data structures.
- Converted the records into a pandas DataFrame.
- Added a UTC collection timestamp.
- Inspected the DataFrame using `head()`, `shape`, `columns`, `dtypes`, `info()`, and `describe()`.

The initial DataFrame contains one row per cryptocurrency with these fields:

| Column | Description |
| --- | --- |
| `coin` | CoinGecko cryptocurrency ID |
| `price` | Latest price in USD |
| `chg_24h` | 24-hour price change percentage |
| `timestamp` | UTC time when the script collected the response |

## Run locally

1. Clone this repository.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Run the extraction script:

   ```bash
   python fetch.py
   ```

The script makes a live API request, so the returned prices and percentage changes will vary. API access and rate limits are controlled by CoinGecko.

## Project structure

```text
realtime-crypto-analytics/
├── fetch.py
├── test_environment.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Planned milestones

- [ ] Expand collection to additional cryptocurrencies.
- [ ] Add timeout handling, retries, and structured logging.
- [ ] Design SQL Server database tables and persist observations.
- [ ] Clean and validate the collected data.
- [ ] Calculate trends, percentage changes, volatility, and anomaly flags.
- [ ] Build an interactive Power BI dashboard.
- [ ] Automate the pipeline and document the results.

## Notes

- Do not commit virtual environments, local databases, logs, API keys, or credentials.
- This project is designed as a near-real-time analytics pipeline; the refresh interval will be set with API rate limits and project requirements in mind.
- No performance or trading recommendations are produced by this project.
