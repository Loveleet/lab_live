# PostgreSQL credentials from environment or keys1_postgresql_local.py. Do not commit real values.
# Set DATABASE_URL or DB_* in env, or create utils/keys1_postgresql_local.py (gitignored) with your host/user/password.

import os

def _pg_url(db_name=None):
    base = os.environ.get("DATABASE_URL")
    if base and not db_name:
        return base
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

connection_string_olab = None  # Set in keys1_postgresql_local.py or used by Final_olab_database from env

# Override from local file (same dir as this file) so DB works without env vars
try:
    _dir = os.path.dirname(os.path.abspath(__file__))
    _local_path = os.path.join(_dir, "keys1_postgresql_local.py")
    if os.path.isfile(_local_path):
        import importlib.util
        _spec = importlib.util.spec_from_file_location("keys1_postgresql_local", _local_path)
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        if getattr(_mod, "connection_string_postgresql", None):
            connection_string_postgresql = _mod.connection_string_postgresql
            connection_string_postgresql_backup1 = connection_string_postgresql
            connection_string_postgresql_backup2 = connection_string_postgresql
            connection_string = connection_string_postgresql
        if getattr(_mod, "POSTGRESQL_CONFIG", None):
            POSTGRESQL_CONFIG = _mod.POSTGRESQL_CONFIG
        if getattr(_mod, "connection_string_postgresql_backtest_db", None):
            connection_string_postgresql_backtest_db = _mod.connection_string_postgresql_backtest_db
        if getattr(_mod, "connection_string_olab", None):
            connection_string_olab = _mod.connection_string_olab
except Exception:
    pass

POSTGRESQL_POOL_CONFIG = {
    "pool_size": 50,
    "max_overflow": 20,
    "pool_timeout": 60,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}
