# Why the dashboard shows no data (and how to fix it)

## Debug first

Open **http://150.241.244.130:10000/api/debug** in the browser. You’ll see:

- **counts**: row counts for `alltraderecords`, `machines`, `pairstatus`
- **dbSource**: `"DATABASE_URL (e.g. Render)"` if the app is using Render’s DB, or `"DB_* / local"` if it’s using the local DB on the cloud server
- **hint**: if the cloud shows very few trades, the hint explains that you need to set `DATABASE_URL` in `/etc/lab-trading-dashboard.env` and restart

The app also loads env from **/etc/lab-trading-dashboard.env** at startup, so adding `DATABASE_URL` there (and restarting) is enough for the cloud to use Render’s database and show the same trades as Vercel/Render.

## Why cloud shows fewer trades than Vercel/Render (same code, different DB)

| Where you open the app | Database the API uses | What you see |
|------------------------|------------------------|--------------|
| **lab-anish.vercel.app** or Render | Database A (full data, e.g. 927 trades) | 313 closed, 927 total, etc. |
| **150.241.244.130:10000** (cloud) | Database B = local `labdb2` on cloud server | Only 2 trades (seed rows) |

The frontend and backend code are the same. The cloud backend reads from local PostgreSQL on the cloud host; that DB has only 2 rows in `alltraderecords`. To see the same data as Render, either **point the cloud at Render’s database** (easiest) or copy/restore the DB — see below.

## Fix: Use Render’s database on the cloud (so cloud shows all the same data)

1. In **Render Dashboard** → your backend service → **Environment** (or the Postgres instance) → copy the **External Database URL** (or Internal if the cloud server can reach it). It looks like:
   `postgres://user:password@host:port/database?sslmode=require`
2. On the **cloud server** (150.241.244.130), edit the app env:
   ```bash
   sudo nano /etc/lab-trading-dashboard.env
   ```
   Add or set (paste your Render URL; use quotes if it contains special chars):
   ```
   DATABASE_URL=postgres://user:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/dbname
   ```
   Remove or comment out `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` if you had them (so `DATABASE_URL` is used).
3. Restart the app:
   ```bash
   sudo systemctl restart lab-trading-dashboard
   ```
4. Refresh **http://150.241.244.130:10000** — the cloud will now use the same database as Render and show all the same trades.

If the cloud server **cannot** reach Render’s database (e.g. Render only allows internal connections), use one of the options below to copy or restore the DB onto the cloud.

## Cause (on the cloud)

On the app server (150.241.244.130), the database `labdb2` has:

- **alltraderecords**: **2 rows** (seed only) → dashboard shows only 2 trades; full data is in the other DB (Vercel/Render source)
- **machines**: 9 rows ✅
- **pairstatus**: 528 rows ✅

So the main “data” (trades) is missing because **alltraderecords is empty**. The app and API are working; there is simply no trade data in the local DB.

## Fix (choose one)

### Option 1: Copy the database from the DB server (recommended)

1. On the **DB server** (150.241.245.36):
   - Allow PostgreSQL from the app server: open **port 5432** for IP **150.241.244.130** (firewall / security group).
   - In `postgresql.conf`: `listen_addresses = '*'` (or include the app server).
   - In `pg_hba.conf`: add  
     `host  labdb2  postgres  150.241.244.130/32  scram-sha-256`

2. From your laptop (repo root):
   ```bash
   ./scripts/copy-database-to-cloud.sh
   ```
   This runs on the app server as root in `/opt`, dumps from 150.241.245.36, restores into local `labdb2`, and restarts the app.

3. Refresh **http://150.241.244.130:10000** — trades should appear.

### Option 2: Use the remote DB directly (no copy)

If you prefer the app to read from the DB server every time:

1. On the **DB server** (150.241.245.36): open port 5432 for 150.241.244.130 and set `listen_addresses` + `pg_hba.conf` as above.

2. On the **app server**, edit `/etc/lab-trading-dashboard.env`:
   ```bash
   DB_HOST=150.241.245.36
   # keep: DB_PORT=5432, DB_USER=postgres, DB_PASSWORD=IndiaNepal1-, DB_NAME=labdb2
   ```

3. Restart the app:
   ```bash
   sudo systemctl restart lab-trading-dashboard
   ```

4. Refresh **http://150.241.244.130:10000**.

### Option 3: One-command dump + restore (when you can reach the full DB from your laptop)

If the database with all the trades is reachable from your machine (e.g. Render’s public DB URL or 150.241.245.36 when 5432 is open from your network):

1. In **.env** set (use the same host/password as the app that shows 927 trades):
   ```
   FULL_DB_HOST=your-postgres-host
   FULL_DB_USER=postgres
   FULL_DB_PASSWORD=yourpassword
   FULL_DB_NAME=labdb2
   ```
2. From repo root run:
   ```bash
   ./scripts/dump-and-restore-to-cloud.sh
   ```
   This dumps from that host, uploads the dump to the cloud server, restores it there, and restarts the app.

3. Refresh **http://150.241.244.130:10000** and check **http://150.241.244.130:10000/api/debug** — `alltraderecords` count should match the other deployment.

### Option 4: Manual dump + restore

If you cannot reach the full DB from your laptop (e.g. Render internal DB only):

1. **Create a dump** from wherever you can run `pg_dump` (e.g. a Render shell or the DB server):
   ```bash
   PGPASSWORD='YourPassword' pg_dump -h <HOST> -U postgres -d labdb2 -F c -f labdb2.dump
   ```
2. **Copy the dump to the cloud server**: `scp labdb2.dump root@150.241.244.130:/tmp/labdb2.dump`
3. **Restore on the cloud**:
   ```bash
   scp scripts/restore-db-on-server.sh root@150.241.244.130:/tmp/
   ssh root@150.241.244.130 'sudo bash /tmp/restore-db-on-server.sh /tmp/labdb2.dump'
   ```
4. Refresh **http://150.241.244.130:10000**.

---

Until the cloud server’s `labdb2` is filled with the full data (by copy script, opening 150.241.245.36:5432, or restoring a dump), the cloud dashboard will keep showing only the rows that exist in the cloud DB (e.g. 2 seed trades).
