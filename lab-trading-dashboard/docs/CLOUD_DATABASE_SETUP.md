# Connect Cloud Server to Your Database (so data shows like on Render)

On **Render**, your app was connected to a database (Render PostgreSQL or an external one). On your **cloud server** (150.241.244.130), the API is not connected to that database yet, so the dashboard shows zeros.

---

## 1. Get your database details

From your **Render** dashboard:

- If you used **Render PostgreSQL**: open the database service → **Info** or **Connect** and note:
  - **Host**
  - **Port** (usually 5432)
  - **Database name**
  - **User**
  - **Password** (or reset it to get a new one)

- If you used an **external database** (e.g. your own Postgres, Supabase, etc.), use that host, port, database, user, and password.

---

## 2. Put them on the cloud server

SSH into the server and edit the env file:

```bash
ssh root@150.241.244.130
sudo nano /etc/lab-trading-dashboard.env
```

Add or update these lines (use your real values):

```env
PORT=10000
DB_HOST=your-database-host.example.com
DB_PORT=5432
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_database_name
```

- **Render PostgreSQL**: the host is often something like `dpg-xxxxx-a.oregon-postgres.render.com` and you may need **SSL**. The server code tries SSL first; if it still fails, we can add `DB_SSL=true` later.
- Save (Ctrl+O, Enter) and exit (Ctrl+X).

---

## 3. Restart the API

```bash
sudo systemctl restart lab-trading-dashboard
```

Check that it connects:

```bash
journalctl -u lab-trading-dashboard -n 30 -f
```

You should see something like `Connected to PostgreSQL successfully`. If you see connection errors, the host/password/firewall or SSL may need adjusting.

---

## 4. Reload the dashboard

Refresh **http://150.241.244.130:10000**. The dashboard should now show the same data as when you were using Render, because the cloud API is using the same database.
