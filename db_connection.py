"""SQLAlchemy engine for the local SQL Server Express database."""

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

connection_string = URL.create(
    "mssql+pyodbc",
    query={
        "odbc_connect": (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=HPAVILION0022\\SQLEXPRESS;"
            "DATABASE=CryptoAnalyticsDB;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
    },
)

engine = create_engine(connection_string)


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
