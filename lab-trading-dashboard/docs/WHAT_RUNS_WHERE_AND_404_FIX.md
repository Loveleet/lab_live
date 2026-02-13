# What runs where — and fixing "Failed to fetch" / 404 on Live Trade

## What runs WHERE

### In the browser (here — GitHub Pages)

- **URL:** https://loveleet.github.io/lab_live/
- **What it is:** The **frontend only** (React/Vite app). It’s static files (HTML, JS, CSS) served by GitHub Pages.
- **What it does:** Renders the dashboard, Live Trade view, charts, etc. It **calls your API** for all data; it does **not** talk to the database or Python directly.

So: **“here” = only the UI. No API, no DB, no api_signals.py.**

---

### On the cloud server (150.241.244.130 / api.clubinfotech.com)

Everything below runs on **your cloud machine** (e.g. Ubuntu). Nginx in front listens on 80/443 and forwards to the Node app.

| Component | What it does | Port / URL |
|-----------|--------------|------------|
| **Nginx** | Terminates HTTPS, forwards requests to Node | 80, 443 → `http://127.0.0.1:10000` |
| **Node server (server.js)** | Main API: `/api/trades`, `/api/trade`, `/api/machines`, etc. Reads/writes **PostgreSQL** (`olab`). Can proxy to Python for signals. | Listens on **10000** |
| **PostgreSQL** | Database: tables like `alltraderecords`, `machines`, `signalprocessinglogs`. | Usually 5432 (local or same host) |
| **api_signals.py (Python)** | Flask app: `/api/calculate-signals`, `/api/sync-open-positions`, etc. Does signal calculation and Binance sync. | Listens on **5001** (or `PYTHON_SIGNALS_PORT`) |

So: **“in the cloud” = Nginx + Node + (optionally) Python + PostgreSQL.**

---

## How the frontend gets data

1. You open **https://loveleet.github.io/lab_live/** or **clubinfotech.com** (redirects to GitHub Pages).
2. The app loads and uses **API base URL** = **https://api.clubinfotech.com** (from `api-config.json` or build).
3. All data requests go to that base URL, for example:
   - **GET /api/trades** — list of trades (from Node → PostgreSQL `alltraderecords`)
   - **GET /api/trade?unique_id=...** — single trade for Live Trade view (Node → PostgreSQL)
   - **POST /api/calculate-signals** — compute signals (Node **proxies** to **api_signals.py** on port 5001)

So:

- **/api/trade** and **/api/trades** are served by **Node** (and the database). They do **not** come from api_signals.py.
- **/api/calculate-signals** is implemented in **api_signals.py**; Node just proxies to it. If api_signals.py isn’t running, that **specific** feature (signals calculation) fails; the 404 you saw is for **/api/trade**, which is a **Node** route.

---

## Why you see "Failed to fetch" and 404 on `/api/trade`

The console shows:

- **404** on: `https://api.clubinfotech.com/api/trade?unique_id=ICXUSDTSELL...`

So the **request is reaching api.clubinfotech.com**, but the server responds with **404 Not Found**. That usually means one of:

1. **Node is not running** on the cloud (port 10000). Then nginx might be returning 404 or 502.
2. **Nginx is not proxying** `/api/*` to Node (wrong or disabled config).
3. **Node is running but something in front** (e.g. another proxy or nginx location) is catching the request and returning 404.

**api_signals.py is not responsible for /api/trade.** So even if api_signals.py is running, the 404 for `/api/trade` will not be fixed by it. You need **Node** to be running and reachable for that URL.

---

## Step-by-step: fix 404 for `/api/trade`

### 1. Check Node is running on the cloud

SSH in and check the process and port:

```bash
ssh root@150.241.244.130

# Is the app running?
sudo systemctl status lab-trading-dashboard

# Is anything listening on 10000?
sudo ss -tlnp | grep 10000
```

- If the service is **inactive**, start it:  
  `sudo systemctl start lab-trading-dashboard`
- If it crashes, check logs:  
  `sudo journalctl -u lab-trading-dashboard -n 100 --no-pager`

### 2. Check nginx is proxying to Node

```bash
# Config that should apply to api.clubinfotech.com
sudo cat /etc/nginx/sites-enabled/lab-trading
```

You should see a `server` block for `api.clubinfotech.com` with something like:

```nginx
location / {
    proxy_pass http://127.0.0.1:10000;
    ...
}
```

So **all** paths (including `/api/trade`) go to Node. If there is no such block, or `proxy_pass` points elsewhere, fix the config, then:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Test `/api/trade` from the server

On the cloud box:

```bash
# Replace with a real unique_id from your DB
curl -s "http://127.0.0.1:10000/api/trade?unique_id=ICXUSDTSELL2025-02-03%2012:57:15" | head -c 500
```

- If you get **JSON** with `{"trade": {...}}` or `{"trade": null}`, Node and the route are OK; the 404 is likely between the internet and Node (nginx/host).
- If you get **404** from this `curl`, then Node isn’t registering the route (e.g. wrong server file or app not restarted).
- If you get **connection refused**, Node isn’t listening on 10000.

### 4. Test from outside (your laptop)

```bash
curl -s "https://api.clubinfotech.com/api/trade?unique_id=ICXUSDTSELL2025-02-03%2012:57:15" | head -c 500
```

- If this returns 404 but step 3 returns 200, the problem is nginx or DNS (e.g. wrong server block or wrong host).
- If both 3 and 4 return 200, the browser 404 may be caching or a different URL (check exact request in DevTools → Network).

### 5. Database and `unique_id`

Node’s `/api/trade` does:

```sql
SELECT * FROM alltraderecords WHERE unique_id = $1 OR "Unique_ID" = $1 LIMIT 1
```

- If the row doesn’t exist, Node still returns **200** with `{"trade": null}` (not 404).
- So a **404** is almost certainly from **before** Node (nginx) or Node not running, not from “trade not found”.

---

## What about api_signals.py?

- **Purpose:** Serves **/api/calculate-signals** (and related endpoints). Used for the **signals** / “Binance Data” calculation, not for loading a single trade by `unique_id`.
- **Where it runs:** On the **same cloud server**, on port **5001** (or `PYTHON_SIGNALS_PORT`).
- **How the frontend uses it:** When not on localhost, the frontend calls **https://api.clubinfotech.com/api/calculate-signals** (same host as the main API). Node receives that and **proxies** to `http://127.0.0.1:5001` (or `PYTHON_SIGNALS_URL`).

So for **api_signals.py** to work in production:

1. **Run it on the cloud**, e.g.:
   ```bash
   cd /path/to/lab-trading-dashboard/python
   PYTHON_SIGNALS_PORT=5001 python api_signals.py
   ```
   (Or run it under systemd/supervisor so it restarts.)

2. **Configure Node** to know the Python URL. In the env loaded by Node (e.g. `/etc/lab-trading-dashboard.secrets.env` or same file as other secrets):
   ```bash
   PYTHON_SIGNALS_URL=http://127.0.0.1:5001
   ```
   Then restart Node:  
   `sudo systemctl restart lab-trading-dashboard`

3. **No nginx change needed** for Python: the browser only talks to api.clubinfotech.com; Node proxies to Python internally.

If **api_signals.py** is not running or `PYTHON_SIGNALS_URL` is wrong, you get failures only on **/api/calculate-signals** (and related), not 404 on **/api/trade**.

---

## One-page summary

| What | Where it runs | Serves |
|------|----------------|--------|
| **Frontend (React)** | GitHub Pages (browser) | UI only; calls api.clubinfotech.com |
| **Nginx** | Cloud | HTTPS, forwards to Node :10000 |
| **Node (server.js)** | Cloud :10000 | /api/trades, **/api/trade**, /api/machines, proxy to Python |
| **PostgreSQL** | Cloud | alltraderecords, machines, etc. |
| **api_signals.py** | Cloud :5001 | /api/calculate-signals, sync-open-positions |

- **404 on /api/trade** → Fix **Node** and **nginx** (steps 1–4). Not api_signals.py.
- **“Failed to fetch” for Binance Data / signals** → Ensure **api_signals.py** is running and **PYTHON_SIGNALS_URL** is set and Node restarted.

After Node is running and nginx is correct, **https://api.clubinfotech.com/api/trade?unique_id=...** should return 200 (with `trade` or `null`), and the Live Trade view can stop showing "Failed to fetch" for that request.
