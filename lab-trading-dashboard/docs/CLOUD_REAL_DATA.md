# Get real data on the cloud (same as Render)

## The issue

| App | Database | What you see |
|-----|----------|--------------|
| **Render / Vercel** | Render Postgres (or your full DB) | Real data — 500+ trades |
| **Cloud (150.241.244.130)** | Local PostgreSQL on the server | Only 2 seed rows (or “demo data hidden”) |

The cloud is **not broken**. It is using a **different database** than Render. Same code, different data source.

---

## Fix in 3 steps (use Render’s DB on the cloud)

### 1. Get Render’s database URL

- Go to **Render Dashboard** → your **Postgres** service (or the service that has the DB).
- Open **Connect** → copy **External Database URL**.
- It looks like: `postgres://USER:PASSWORD@dpg-xxxxx.oregon-postgres.render.com:5432/dbname`

### 2. Set it on the cloud server

```bash
ssh root@150.241.244.130
sudo nano /etc/lab-trading-dashboard.env
```

Add **one line** (paste your URL; use single quotes if the password has special characters):

```bash
DATABASE_URL='postgres://USER:PASSWORD@dpg-xxxxx.oregon-postgres.render.com:5432/dbname'
```

- Remove or comment out any `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` so only `DATABASE_URL` is used.
- Save and exit (Ctrl+O, Enter, Ctrl+X).

### 3. Restart and check

```bash
sudo systemctl restart lab-trading-dashboard
```

Wait ~30 seconds, then:

```bash
curl http://150.241.244.130:10000/api/debug
```

You should see:

- `"dbSource": "DATABASE_URL (e.g. Render)"`
- `"counts": { "alltraderecords": 500+, ... }`

Then open **http://150.241.244.130:10000** in the browser — you should see the same real data as Render.

---

## If it still doesn’t work

- **“Database not connected” or timeout**  
  Check logs: `ssh root@150.241.244.130 'journalctl -u lab-trading-dashboard -n 80 --no-pager'`  
  Look for connection errors (wrong URL, firewall, SSL).

- **Render only allows “Internal” URL**  
  Then the cloud server cannot reach Render’s DB. Use one of: copy DB to cloud, dump/restore, or use a DB that is reachable from the cloud (see [DATA_NOT_SHOWING.md](./DATA_NOT_SHOWING.md)).
