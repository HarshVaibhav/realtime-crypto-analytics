"""SQLAlchemy engine configured through local environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Load the .env file beside this script. Environment variables already set
# by the operating system take precedence over values in the file.
load_dotenv(Path(__file__).resolve().parent / ".env")


def _required_setting(name):
    """Return a required environment setting or raise a helpful error."""
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing required setting: {name}. "
            "Copy .env.example to .env and configure your SQL Server settings."
        )
    return value.strip()


server = _required_setting("SQL_SERVER")
database = os.getenv("SQL_DATABASE", "CryptoAnalyticsDB").strip()
driver = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server").strip()
trusted_connection = (
    os.getenv("SQL_TRUSTED_CONNECTION", "yes").strip().lower()
    in {"yes", "true", "1"}
)
trust_server_certificate = (
    os.getenv("SQL_TRUST_SERVER_CERTIFICATE", "yes").strip().lower()
    in {"yes", "true", "1"}
)

connection_options = {
    "driver": driver,
    "TrustServerCertificate": "yes" if trust_server_certificate else "no",
}

if trusted_connection:
    connection_options["trusted_connection"] = "yes"
    connection_url = URL.create(
        "mssql+pyodbc",
        host=server,
        database=database,
        query=connection_options,
    )
else:
    username = _required_setting("SQL_USERNAME")
    password = _required_setting("SQL_PASSWORD")
    connection_url = URL.create(
        "mssql+pyodbc",
        username=username,
        password=password,
        host=server,
        database=database,
        query=connection_options,
    )

engine = create_engine(connection_url)


if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            result = connection.exec_driver_sql("SELECT DB_NAME()")
            print("Database connection successful!")
            print("Connected Database:", result.scalar())
    except Exception as error:
        print("Database connection failed:")
        print(error)
    finally:
        engine.dispose()
