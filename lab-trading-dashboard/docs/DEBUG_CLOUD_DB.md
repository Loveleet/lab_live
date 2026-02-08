# Cloud + database debug report (step-by-step)

## Step 1: Is the cloud running server.js?

**Result:** Yes. Process on cloud: `/usr/bin/node server.js`

---

## Step 2: Which server.js file is used?

**Result:** The app is running from `/opt/apps/lab-trading-dashboard/server`. The file `server.js` there is the deployed template (no Render; cloud-only comment in header). So the cloud is running the correct server.

---

## Step 3 & 4: Which database config does the server use?

**Result:** The server uses `/etc/lab-trading-dashboard.env` with:

- `DB_HOST=localhost`
- `DB_PORT=5432`
- `DB_USER=postgres`
- `DB_NAME=labdb2`

So the server is configured to use **PostgreSQL on the same machine (localhost)**, not a remote DB.

---

## Step 5: Does the server reach the database?

**Result:** Yes. `GET /api/debug` returns:

- `ok: true`
- `counts: { alltraderecords: 2, machines: 9, pairstatus: 528 }`
- `dbSource: "DB_* / local"`

So the server **is** connecting to a database and reading from it.

---

## Step 6: How many rows are in the database?

**Result:** On the cloud, direct query: `SELECT count(*) FROM alltraderecords` → **2 rows**.

So the database the app is using (localhost `labdb2`) **only has 2 rows** in `alltraderecords`. That is why you see “demo” data: the app is showing everything that is in that DB.

---

## Step 7: Can the cloud reach the other DB server (150.241.245.36)?

**Result:** From the cloud server, **port 5432 on 150.241.245.36 is not reachable** (connection test failed). So either:

- Postgres on 150.241.245.36 is not listening for remote connections, or  
- A firewall is blocking the cloud (150.241.244.130) from 150.241.245.36:5432.

---

## Summary

| Check | Status |
|-------|--------|
| Cloud runs `server.js` | Yes |
| Correct `server.js` (deployed template) | Yes |
| Server reads env from `/etc/lab-trading-dashboard.env` | Yes |
| DB config | `DB_HOST=localhost` → local Postgres |
| Server connects to DB | Yes |
| Rows in `alltraderecords` (local DB) | 2 |
| Cloud → 150.241.245.36:5432 | Not reachable |

So: the cloud **is** running server.js and **is** reaching **a** database; that database is **local** and has only **2 rows**. The machine that likely has the full data (150.241.245.36) is **not** reachable from the cloud on port 5432.

---

## How to get real data (choose one)

**Option A – Use the remote DB (150.241.245.36) when it’s reachable**

1. On **150.241.245.36**: allow Postgres from the cloud (open port 5432 for 150.241.244.130, set `listen_addresses` and `pg_hba.conf`).
2. On the **cloud** (150.241.244.130):  
   `sudo nano /etc/lab-trading-dashboard.env`  
   Set:
   - `DB_HOST=150.241.245.36`
   - Keep `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` correct for that server.
3. Restart: `sudo systemctl restart lab-trading-dashboard`.  
   Then the app will use the DB on 150.241.245.36 and show its data.

**Option B – Copy the full DB into the cloud’s local Postgres**

1. From your laptop (or a host that can reach 150.241.245.36 and the cloud), run a dump from 150.241.245.36 and restore into the cloud’s local `labdb2` (e.g. using `scripts/dump-and-restore-to-cloud.sh` or similar).
2. Restart the app on the cloud.  
   Then the app keeps using `DB_HOST=localhost` but the local `labdb2` will have the full data.

Nothing in this flow uses Render; the app runs only on the cloud and talks only to the DB you configure.
