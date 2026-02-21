# Binance and DB credentials from environment. Do not commit real values.
# Set BINANCE_API_KEY, BINANCE_SECRET (and DB_*) in env, or use a local keys1_local.py (gitignored).

import os

api = os.environ.get("BINANCE_API_KEY", "")
secret = os.environ.get("BINANCE_SECRET", "")

# Fallback: load keys1_local.py from same directory (gitignored) so open-position works without env
if not api or not secret:
    try:
        _dir = os.path.dirname(os.path.abspath(__file__))
        _local_path = os.path.join(_dir, "keys1_local.py")
        if os.path.isfile(_local_path):
            import importlib.util
            _spec = importlib.util.spec_from_file_location("keys1_local", _local_path)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            if getattr(_mod, "api", None):
                api = _mod.api
            if getattr(_mod, "secret", None):
                secret = _mod.secret
    except Exception:
        pass

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
