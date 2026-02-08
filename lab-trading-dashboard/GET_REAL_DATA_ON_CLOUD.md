# Get real data on the cloud site

The **Node.js server (server.js) runs only on your cloud** at 150.241.244.130. To show real data, point it at your Postgres database.

---

## 1. Get your Postgres database URL

Use the connection URL for the database that has your trade data. It looks like:

`postgres://user:password@host:5432/dbname`

(If your DB is on another host, use that host in the URL.)

---

## 2. On the cloud server: set `DATABASE_URL` and restart

SSH in and edit the env file:

```bash
ssh root@150.241.244.130
sudo nano /etc/lab-trading-dashboard.env
```

**Add one line** (paste your Postgres URL; use single quotes if the password has special characters):

```bash
DATABASE_URL='postgres://USER:PASSWORD@your-db-host:5432/dbname'
```

- Remove or comment out any existing `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
- Save and exit: `Ctrl+O`, `Enter`, `Ctrl+X`.

Restart the app:

```bash
sudo systemctl restart lab-trading-dashboard
```

---

## 3. Check

Wait about 30 seconds, then:

- Open **http://150.241.244.130:10000** in the browser → you should see real data.
- Or run: `curl http://150.241.244.130:10000/api/debug`  
  You should see `"dbSource": "DATABASE_URL (remote)"` and a non-zero `alltraderecords` count.

---

If you still don’t see real data, check logs on the server:

```bash
journalctl -u lab-trading-dashboard -n 80 --no-pager
```

Look for connection errors (wrong URL, firewall, or SSL). More options: **docs/CLOUD_REAL_DATA.md** and **docs/DATA_NOT_SHOWING.md**.
