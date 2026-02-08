# LAB Trading Dashboard — Architecture, Flow & Where Secrets Live

## High-level flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  YOUR BROWSER                                                                 │
│  You open:  http://150.241.244.130:10000                                     │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLOUD SERVER (Ubuntu) — 150.241.244.130                                     │
│  Port 10000 — ONE Node.js process (Express)                                   │
│                                                                               │
│  1) Serves FRONTEND (React/Vite build)                                         │
│     - Static files from  /opt/apps/lab-trading-dashboard/dist/               │
│     - index.html, JS, CSS — no separate “frontend server”                     │
│                                                                               │
│  2) Serves BACKEND (API)                                                      │
│     - Same process, routes like  /api/trades,  /api/machines,  /api/debug     │
│     - When DB is unreachable → proxies from Render (fallback)                 │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────────────┐
        │  Direct DB (optional)  │       │  RENDER (fallback)             │
        │  150.241.245.36:5432  │       │  https://lab-anish.onrender.com │
        │  Postgres             │       │  Same backend code, has DB      │
        │  (currently blocked)   │       │  → cloud proxies its /api/*    │
        └───────────────────────┘       └───────────────────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────────┐
                                        │  Postgres (Render’s DB │
                                        │  or your 150.241.245  │
                                        │  — Render can reach it)│
                                        └───────────────────────┘
```

So: **one URL, one server**. Frontend and backend both live on **150.241.244.130:10000**. The browser loads the React app from there and the same origin calls `/api/*` on the same host.

---

## Where is what

| What | Where |
|------|--------|
| **Frontend (React/Vite)** | Built to `dist/` on your laptop → uploaded to cloud at `/opt/apps/lab-trading-dashboard/dist/`. The Node server serves these static files (and `index.html` for SPA). |
| **Backend (Node/Express)** | Runs on the **same** cloud machine: `server/server.js` (created from `server.example.js`). Port **10000**. |
| **Single entry URL** | **http://150.241.244.130:10000** — this serves both the dashboard UI and all APIs. |

There is no separate “frontend host” in production: the cloud **is** both frontend and backend.

---

## Where are passwords and secrets?

**Rule: secrets are only in env files, never in Git.**

| Secret / config | Where it lives | In Git? |
|-----------------|----------------|--------|
| **Cloud server (150.241.244.130)** | | |
| DB connection (DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME) | **On cloud only:** `/etc/lab-trading-dashboard.env` | No |
| FALLBACK_API_URL (Render URL for fallback data) | Same file: `/etc/lab-trading-dashboard.env` | No |
| **Laptop (your machine)** | | |
| SSH to cloud (DEPLOY_HOST, DEPLOY_PASSWORD) | Your **local** `.env` in the repo root | No (`.env` is gitignored) |
| DB server SSH (DB_SERVER, DB_SERVER_PASSWORD) | Same local `.env` | No |
| **Codebase (GitHub)** | | |
| `server.example.js` | Template only — **no** passwords; has defaults like `IndiaNepal1-` only for the *remote* DB host in code | Yes (safe: no real secrets) |
| `server.js` | **Not in Git** — created on the cloud from `server.example.js` at deploy time | No (gitignored) |
| `.env` | **Not in Git** — used only on your laptop for deploy scripts | No (gitignored) |

So:

- **Cloud:** all runtime secrets (DB, FALLBACK_API_URL) → **`/etc/lab-trading-dashboard.env`** (read by systemd and by the server at startup).
- **Laptop:** deploy and SSH credentials → **`.env`** in the project root (only for scripts like `upload-dist.sh`, never committed).

---

## How the server loads env (cloud)

On startup the Node server (in order):

1. Tries to load `.env` from `server/` and from project root (for local runs).
2. Tries to load **`/etc/lab-trading-dashboard.env`** (main file on the cloud).

Systemd also passes this file to the process:

```ini
EnvironmentFile=-/etc/lab-trading-dashboard.env
ExecStart=/usr/bin/node server.js
```

So **all passwords and config for the running app** come from **`/etc/lab-trading-dashboard.env`** on the cloud (and optionally from `.env` on your machine when you run scripts).

---

## Data flow (why the dashboard “works now”)

1. You open **http://150.241.244.130:10000** → browser gets the React app from the cloud (same origin).
2. React calls **http://150.241.244.130:10000/api/trades**, **/api/machines**, etc. (same origin; `src/config.js` uses empty base URL in production on that host).
3. Cloud backend:
   - Tries to connect to Postgres (e.g. 150.241.245.36). If that fails (e.g. port closed), `pool` stays `null`.
   - When `pool` is `null` and **FALLBACK_API_URL** is set (e.g. `https://lab-anish.onrender.com`), the server **proxies** those API calls to Render: it fetches `/api/trades`, `/api/machines`, etc. from Render and returns the same JSON.
4. So the dashboard shows the **same data** Render has (Render talks to the DB; your cloud talks to Render when it can’t talk to the DB).

No passwords are sent to the browser; the browser only talks to your cloud. The cloud uses its env (and optionally Render) to get data.

---

## Summary

| Question | Answer |
|----------|--------|
| Where is the frontend? | On the cloud at 150.241.244.130:10000, served as static files from `dist/`. |
| Where is the backend? | Same machine, same port 10000; one Express app serves both static and `/api/*`. |
| Where are passwords saved? | **Cloud:** `/etc/lab-trading-dashboard.env`. **Laptop:** `.env` (deploy/SSH only). Neither is in Git. |
| How does data get to the dashboard when DB is unreachable? | Backend uses **FALLBACK_API_URL** and proxies `/api/trades`, `/api/machines`, etc. from Render (which can reach the DB). |
