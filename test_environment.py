"""Check required packages, local configuration, and SQL ODBC driver."""

from pathlib import Path
import importlib
import os

PROJECT_DIR = Path(__file__).resolve().parent
ENV_FILE = PROJECT_DIR / ".env"

REQUIRED_MODULES = ["requests", "pandas", "sqlalchemy", "pyodbc", "dotenv"]


def main():
    print("--- ENVIRONMENT CHECK ---")
    failed = False

    for module_name in REQUIRED_MODULES:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "installed")
            print(f"[OK] {module_name}: {version}")
        except ImportError as error:
            failed = True
            print(f"[MISSING] {module_name}: {error}")

    # Load .env only after confirming python-dotenv is importable.
    if "dotenv" in __import__("sys").modules:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE)

    if ENV_FILE.exists():
        print("[OK] Local .env file found.")
    else:
        failed = True
        print("[MISSING] .env file. Copy .env.example to .env.")

    server = os.getenv("SQL_SERVER", "").strip()
    database = os.getenv("SQL_DATABASE", "").strip()
    driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server").strip()

    if server:
        print("[OK] SQL_SERVER is configured.")
    else:
        failed = True
        print("[MISSING] SQL_SERVER is not configured.")

    if database:
        print(f"[OK] SQL_DATABASE is configured: {database}")
    else:
        failed = True
        print("[MISSING] SQL_DATABASE is not configured.")

    try:
        import pyodbc
        installed_drivers = pyodbc.drivers()
        if driver in installed_drivers:
            print(f"[OK] ODBC driver is installed: {driver}")
        else:
            failed = True
            print(f"[MISSING] ODBC driver not found: {driver}")
            print("Installed ODBC drivers:", installed_drivers)
    except ImportError:
        failed = True
        print("[MISSING] pyodbc is not installed; cannot inspect ODBC drivers.")

    if failed:
        print("\nEnvironment check completed with issues.")
        raise SystemExit(1)

    print("\nAll environment checks passed.")
    print("Run python db_connection.py to test the actual database connection.")


if __name__ == "__main__":
    main()
