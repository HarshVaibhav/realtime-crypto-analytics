"""Verify that the project's Python dependencies can be imported."""

import requests
import pandas as pd
import sqlalchemy
import pyodbc
from dotenv import load_dotenv

print("All libraries imported successfully!")
print("Pandas version:", pd.__version__)
