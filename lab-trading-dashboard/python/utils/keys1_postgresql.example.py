# Copy to keys1_postgresql.py and set DATABASE_URL or DB_* env vars. Do not commit keys1_postgresql.py.

import os

def _pg_url(db_name=None):
    url = os.environ.get("DATABASE_URL")
    if url and not db_name:
        return url
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = os.environ.get("DB_PORT", "5432")
    user = os.environ.get("DB_USER", "lab")
    pwd = os.environ.get("DB_PASSWORD", "")
    db = db_name or os.environ.get("DB_NAME", "labdb2")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

connection_string_postgresql = _pg_url()
connection_string_postgresql_backtest_db = os.environ.get("DATABASE_URL_BACKTEST") or _pg_url("backtestdb")
connection_string_postgresql_backup1 = connection_string_postgresql
connection_string_postgresql_backup2 = connection_string_postgresql
connection_string = connection_string_postgresql

POSTGRESQL_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "database": os.environ.get("DB_NAME", "labdb2"),
    "user": os.environ.get("DB_USER", "lab"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "connect_timeout": 300,
    "application_name": "TradingBot",
}

POSTGRESQL_POOL_CONFIG = {
    "pool_size": 50,
    "max_overflow": 20,
    "pool_timeout": 60,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}
