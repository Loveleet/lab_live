# Copy this file to keys1_postgresql_local.py and set your PostgreSQL host, user, password, database.
# keys1_postgresql_local.py is gitignored — it will not be committed.

# Option 1: Full URL (easiest)
connection_string_postgresql = "postgresql://lab:YOUR_PASSWORD@YOUR_HOST:5432/labdb2"
# Examples:
# connection_string_postgresql = "postgresql://lab:yourpass@127.0.0.1:5432/labdb2"
# connection_string_postgresql = "postgresql://lab:yourpass@150.241.244.130:5432/labdb2"

# Optional: backtest DB (if different)
connection_string_postgresql_backtest_db = "postgresql://lab:YOUR_PASSWORD@YOUR_HOST:5432/backtestdb"

# Required for sync-open-positions / exchange_trade (olab database)
connection_string_olab = "postgresql://lab:YOUR_PASSWORD@YOUR_HOST:5432/olab"

# Option 2: Or set POSTGRESQL_CONFIG (used by some code paths)
POSTGRESQL_CONFIG = {
    "host": "127.0.0.1",       # or "150.241.244.130" for remote
    "port": 5432,
    "database": "labdb2",
    "user": "lab",
    "password": "YOUR_PASSWORD",
    "connect_timeout": 300,
    "application_name": "TradingBot",
}
