# Fix cloud server so GitHub Pages shows data

When GitHub Pages (loveleet.github.io/lab_live) shows "No trade records" and zeros, the app is calling your **backend** (cloud server). The cloud must run the latest `server.js` and use the **olab** database. Use a **fixed API URL** (cloud IP or domain); no tunnel.

## 1. Deploy latest server to the cloud

From your laptop (in `lab-trading-dashboard`):

```bash
./scripts/copy-server-to-cloud.sh root 150.241.244.130 /root/lab-trading-dashboard
```

Or copy manually:

```bash
scp server/server.js root@150.241.244.130:/root/lab-trading-dashboard/server/
ssh root@150.241.244.130 "sudo systemctl restart lab-trading-dashboard"
```

(Use your actual server path if different, e.g. `/opt/apps/lab-trading-dashboard/server/`.)

## 2. Cloud secrets: use database **olab** (real data)

On the cloud, edit the secrets file (e.g. `/etc/lab-trading-dashboard.secrets.env`):

- **DB_NAME=olab** (real trading data)
- **DB_HOST**, **DB_USER**, **DB_PASSWORD**, **DB_PORT** as needed

Example:

```bash
# On cloud: sudo nano /etc/lab-trading-dashboard.secrets.env
DB_HOST=150.241.244.130
DB_PORT=5432
DB_USER=lab
DB_PASSWORD=your_password
DB_NAME=olab
PORT=10000
NODE_ENV=production
```

If you don’t set DB_* vars, the server defaults to host **150.241.244.130** and database **olab**.

## 3. Restart the app on the cloud

```bash
sudo systemctl restart lab-trading-dashboard
# Wait ~10s, then check:
curl -s http://localhost:10000/api/health
curl -s http://localhost:10000/api/server-info
curl -s http://localhost:10000/api/trades | head -c 300
```

## 4. Verify config

- **GET /api/server-info** should show:
  - `hasGitHubPagesOrigin: true`
  - `database: "olab"`
  - `message` indicating CORS + olab OK.

- **GET /api/trades** should return a non‑empty `trades` array.

From your laptop (use your backend URL — cloud IP or domain):

```bash
curl -s http://150.241.244.130:10000/api/server-info
curl -s http://150.241.244.130:10000/api/trades
```

## 5. GitHub Pages

- Set GitHub secret **API_BASE_URL** = your backend URL (e.g. `http://150.241.244.130:10000` or `https://your-domain.com`), no trailing slash.
- Run **Deploy frontend to GitHub Pages** (or push to trigger it).
- Open https://loveleet.github.io/lab_live/ and hard‑refresh (Ctrl+Shift+R).

With the cloud running the latest server (CORS + olab) and **API_BASE_URL** set correctly, GitHub Pages will show real data.
