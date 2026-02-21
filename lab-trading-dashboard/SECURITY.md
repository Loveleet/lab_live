# Security — credentials and sensitive data

**Do not commit API keys, passwords, or secrets to the repository.** All sensitive configuration is read from environment variables or local secret files that are not tracked.

## Environment variables

Set these in your environment, `.env`, or (on the server) `/etc/lab-trading-dashboard.secrets.env`:

| Purpose | Variables | Used by |
|--------|-----------|--------|
| **Binance Futures API** | `BINANCE_API_KEY`, `BINANCE_SECRET` | Python `utils/keys1.py`, `main_binance.py` |
| **PostgreSQL (main)** | `DATABASE_URL` or `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT` | Node server, Python `Final_olab_database.py`, `FinalVersionTradingDB_PostgreSQL.py`, `keys1_postgresql.py` |
| **PostgreSQL (olab)** | `OLAB_DATABASE_URL` or same `DB_*` (default db: olab) | Python `Final_olab_database.py` |
| **PostgreSQL (backtest)** | `DATABASE_URL_BACKTEST` or same `DB_*` (db: backtestdb) | Python `backtestdb.py`, `keys1_postgresql.py` |
| **Tmux bot cleaner DB** | `TMUX_DB_HOST`, `TMUX_DB_USER`, `TMUX_DB_PASSWORD`, `TMUX_DB_NAME`, `TMUX_DB_PORT` | `tmux_bot_cleaner.py` |
| **Node server DB** | `DB_PASSWORD`, `DB_HOST`, `DB_USER`, `DB_NAME` | `server.js` (use `server.example.js` as template; real `server.js` is not in repo) |
| **Action password** | Stored in DB table `lab_settings` key `action_password` | Node server for Execute Trade, End Trade, Set Stop Price, etc. |

## Files that must not contain real secrets

- **`python/utils/keys1.py`** — committed version reads only from env; no hardcoded Binance keys or DB passwords.
- **`python/utils/keys1_postgresql.py`** — same; use `keys1_postgresql.example.py` as reference.
- **`server/server.js`** — not in repo (gitignored); use `server.example.js` and set `DB_PASSWORD` etc. in env.
- **`.env`**, **`secrets.env`** — gitignored; create from `.env.example` / `secrets.env.example`.

## After cloning

1. Copy `python/utils/keys1.example.py` and `keys1_postgresql.example.py` for reference (optional; committed `keys1.py` and `keys1_postgresql.py` already use env).
2. Set `BINANCE_API_KEY`, `BINANCE_SECRET`, and DB-related env vars (see table above).
3. For Node: use `server.example.js` as base, set `DB_PASSWORD` and other env vars; do not commit a `server.js` with real credentials.
