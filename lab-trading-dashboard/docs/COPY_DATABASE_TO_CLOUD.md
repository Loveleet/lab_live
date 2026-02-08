# Copy database from 150.241.245.36 to cloud app server

**If the dashboard shows no trades:** the local `alltraderecords` table is empty. See [DATA_NOT_SHOWING.md](DATA_NOT_SHOWING.md) for why and how to fix it.

**Automated script:** From the repo root run `./scripts/copy-database-to-cloud.sh`. It uses `DEPLOY_PASSWORD` and `DB_SERVER_PASSWORD` from `.env`. If SSH to the DB server (150.241.245.36) fails with "Permission denied", that host may use a different root password or key-only auth—set `DB_SERVER_PASSWORD` in `.env` if you have it, or use the manual steps below.

Your **Render** setup used a database that had all the tables and data (`alltraderecords`, `machines`, `active_loss`, `signalprocessinglogs`, etc.).  
On the cloud app server we use a **local** PostgreSQL that was created empty, so the dashboard shows zeros.

To get the same data showing on the cloud, copy the database from the server that has it (**150.241.245.36**) into the app server (**150.241.244.130**).

---

## Option A: You have SSH to the DB server (150.241.245.36)

### Step 1: On the DB server (150.241.245.36)

SSH in and create a dump of `labdb2`:

```bash
ssh root@150.241.245.36

# Dump the database (use postgres user; password: IndiaNepal1-)
PGPASSWORD='IndiaNepal1-' pg_dump -h localhost -U postgres -d labdb2 -F c -f /tmp/labdb2.dump

# Or if PostgreSQL is on another host on that machine:
# PGPASSWORD='IndiaNepal1-' pg_dump -h 127.0.0.1 -U postgres -d labdb2 -F c -f /tmp/labdb2.dump
```

### Step 2: Copy the dump to the app server

From your **laptop** (or from 150.241.245.36 if it can reach 150.241.244.130):

```bash
scp root@150.241.245.36:/tmp/labdb2.dump /tmp/
scp /tmp/labdb2.dump root@150.241.244.130:/tmp/
```

### Step 3: On the app server (150.241.244.130) – restore

```bash
ssh root@150.241.244.130

# Drop existing labdb2 and recreate (so restore is clean)
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'labdb2' AND pid <> pg_backend_pid();"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS labdb2;"
sudo -u postgres psql -c "CREATE DATABASE labdb2 OWNER postgres;"

# Restore the dump
sudo -u postgres pg_restore -d labdb2 -F c /tmp/labdb2.dump

# Restart the app
sudo systemctl restart lab-trading-dashboard
```

Then refresh **http://150.241.244.130:10000** – the dashboard should show the same data as on Render.

---

## Option B: Direct dump from app server (if it can reach 150.241.245.36:5432)

If the app server can connect to the DB server (firewall allows 150.241.244.130 → 150.241.245.36:5432), run this **on the app server**:

```bash
ssh root@150.241.244.130

PGPASSWORD='IndiaNepal1-' pg_dump -h 150.241.245.36 -U postgres -d labdb2 -F c -f /tmp/labdb2.dump
sudo -u postgres psql -c "DROP DATABASE IF EXISTS labdb2;"
sudo -u postgres psql -c "CREATE DATABASE labdb2 OWNER postgres;"
sudo -u postgres pg_restore -d labdb2 -F c /tmp/labdb2.dump
sudo systemctl restart lab-trading-dashboard
```

Then point the app back at the remote DB by editing `/etc/lab-trading-dashboard.env` and setting `DB_HOST=150.241.245.36` again, and restart the service.  
(If you prefer to keep using the local DB, use Option A so the data lives on the app server.)

---

## Summary

| Where data lives | What you did |
|------------------|--------------|
| **Render**       | App connected to a DB that had tables + data. |
| **Cloud now**    | App connected to local PostgreSQL; DB is empty. |
| **Fix**          | Copy that DB (from 150.241.245.36 or from Render export) into the cloud server’s `labdb2`. |

The **server code** is the same; the only difference is **which database** it uses and **whether that database has data**.
