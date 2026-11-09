# Day 1 — Environment Setup and First API Extraction

This folder documents the first working stage of the Real-Time Crypto Analytics Pipeline.

## Day 1 goals

- Create a Python virtual environment.
- Install the project dependencies.
- Verify that the required Python libraries import successfully.
- Call the CoinGecko simple-price API.
- Convert the JSON response into a pandas DataFrame.
- Add a UTC collection timestamp and inspect the extracted data.

## Existing project files used

The executable files are kept in the repository root because later stages import and reuse them. They are linked here rather than duplicated.

| File | Purpose |
| --- | --- |
| [`fetch.py`](../fetch.py) | Fetches cryptocurrency prices from CoinGecko and returns a pandas DataFrame. The current version has evolved to support five assets, retries, validation, and UTC timestamps. |
| [`test_environment.py`](../test_environment.py) | Checks that the project's Python dependencies can be imported. |
| [`requirements.txt`](../requirements.txt) | Lists the Python packages required by the project. |
| [`.gitignore`](../.gitignore) | Excludes virtual environments, secrets, logs, and local database artifacts from Git. |

## Setup commands

Run these commands in the project directory using PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python test_environment.py
python fetch.py
```

## Original Day 1 API scope

The first extraction exercise used the CoinGecko endpoint:

`https://api.coingecko.com/api/v3/simple/price`

Initial assets: Bitcoin (`bitcoin`) and Ethereum (`ethereum`).

Parameters:
- `ids`: `bitcoin,ethereum`
- `vs_currencies`: `usd`
- `include_24hr_change`: `true`

The original exercise focused on reading the API response, building a DataFrame with coin, USD price, and 24-hour change, adding a UTC timestamp, and inspecting the result with pandas.

## Repository note

The root-level `fetch.py` is the maintained project implementation, not a frozen copy of the original Day 1 code. It was expanded in later project stages. Keeping one maintained implementation avoids duplicate scripts and prevents import paths used by the pipeline from breaking.

The exact original Day 1 version was not retained as a separate historical file, so this guide does not claim that the current `fetch.py` is byte-for-byte identical to that first exercise.
