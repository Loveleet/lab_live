# Copy this file to keys1.py and set environment variables, or fill in (do not commit keys1.py).
# Required env vars for Binance: BINANCE_API_KEY, BINANCE_SECRET
# Optional for DB: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT (for ODBC-style connection_string)

import os

# Binance API - set in env or replace below (do not commit real keys)
api = os.environ.get("BINANCE_API_KEY", "your_binance_api_key_here")
secret = os.environ.get("BINANCE_SECRET", "your_binance_secret_here")

# SQL Server ODBC connection string - use env or placeholder (do not commit real credentials)
_db_server = os.environ.get("DB_SERVER", "localhost")
_db_name = os.environ.get("DB_NAME", "labDB2")
_db_user = os.environ.get("DB_USER", "lab")
_db_pwd = os.environ.get("DB_PASSWORD", "")

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={_db_server};"
    f"DATABASE={_db_name};"
    f"UID={_db_user};"
    f"PWD={_db_pwd};"
    "Connection Timeout=120;"
)
connection_string_labdb2 = connection_string
connection_string1 = connection_string
