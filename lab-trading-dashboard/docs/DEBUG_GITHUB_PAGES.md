# Debug GitHub Pages Not Showing Data

When **https://loveleet.github.io/lab_live/** shows "No trade records" but local works, follow this checklist.

The frontend loads the API URL from **api-config.json** (written at deploy from the **API_BASE_URL** secret). Use a **fixed backend URL**: your cloud IP (e.g. `http://150.241.244.130:10000`) or your domain (e.g. `https://api.yourdomain.com`). No tunnel.

---

## Step 1: Check Browser Console (on GitHub Pages)

Open **https://loveleet.github.io/lab_live/** → **F12** → **Console** tab. Look for:

1. **`[LAB] API base URL`** or **`[LAB] API base from api-config.json`** — Should show your backend URL (e.g. `http://150.241.244.130:10000`). If empty, **api-config.json** didn't load or **API_BASE_URL** secret isn't set.

2. **`[LAB] Fetching api-config.json:`** — Should show `https://loveleet.github.io/lab_live/api-config.json`. If you see **404**, the file wasn't deployed correctly.

3. **`[DEBUG] Fetching trades from:`** — Should show full URL like `http://150.241.244.130:10000/api/trades` (or your domain).

4. **`[DEBUG] Trades response status:`** — Check the status:
   - **200 OK** → API works, but data might be empty (check cloud DB).
   - **CORS error** → Cloud server doesn't allow `https://loveleet.github.io` (update server.js on cloud).
   - **404 / Network error** → Backend URL wrong or cloud server down.

5. **Click "Test /api/server-info"** button (debug panel) — Should return JSON with:
   - `hasGitHubPagesOrigin: true`
   - `database: "olab"`
   - `requestOriginAllowed: true`

---

## Step 2: Verify api-config.json is Deployed

Open in browser: **https://loveleet.github.io/lab_live/api-config.json**

Should return JSON like:
```json
{
  "apiBaseUrl": "http://150.241.244.130:10000",
  "tunnelUrl": "http://150.241.244.130:10000"
}
```
(Or your HTTPS domain if you set one.)

If **404**: The deploy workflow didn't place it correctly. Check:
- **GitHub Actions** → **Deploy frontend to GitHub Pages** → latest run → check if "Place api-config.json under base path" step succeeded.

If **empty `{}`**: **API_BASE_URL** secret isn't set in GitHub. Set it to your backend URL (e.g. `http://150.241.244.130:10000`).

---

## Step 3: Verify Cloud Server Config

**On the cloud (150.241.244.130):**

```bash
curl -s http://localhost:10000/api/server-info | python3 -m json.tool
```

Should show:
- `hasGitHubPagesOrigin: true`
- `database: "olab"`
- `allowedOrigins`: includes `https://loveleet.github.io`

If not: deploy latest `server/server.js` to cloud, restart: `sudo systemctl restart lab-trading-dashboard`.

---

## Step 4: Test Backend Directly

From your laptop or browser:

```bash
# Replace with your actual API URL (cloud IP or domain)
curl -s http://150.241.244.130:10000/api/server-info | python3 -m json.tool
curl -s http://150.241.244.130:10000/api/trades | python3 -m json.tool | head -20
```

Should return server-info and a non-empty `trades` array. If this fails, the cloud server or DB is down.

---

## Step 5: Verify GitHub Secret

**GitHub repo** → **Settings** → **Secrets and variables** → **Actions** → **API_BASE_URL**:

- Value = your **backend URL** (e.g. `http://150.241.244.130:10000` or `https://your-domain.com`), **no trailing slash**.
- After changing, run **Deploy frontend to GitHub Pages** workflow.

---

## Step 6: Redeploy Frontend

1. Run **Deploy frontend to GitHub Pages** workflow (or push to trigger it).
2. Hard refresh: **Ctrl+Shift+R** (or **Cmd+Shift+R** on Mac).

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "API base URL" empty | api-config.json not loading or API_BASE_URL not set | Set **API_BASE_URL** secret to backend URL, redeploy frontend |
| api-config.json 404 | File not placed under `/lab_live/` | Check deploy workflow step "Place api-config.json under base path" |
| CORS blocked | Cloud doesn't allow `https://loveleet.github.io` | Deploy latest server.js, restart cloud server |
| 200 but empty trades | Cloud using wrong DB | Set **DB_NAME=olab** in cloud secrets (e.g. `/etc/lab-trading-dashboard.secrets.env`) |
| Network error | Backend URL wrong or server down | Check cloud: `curl http://150.241.244.130:10000/api/health` |

---

## Quick Test (browser console on GitHub Pages)

```javascript
console.log("API Base:", getApiBaseUrl());
fetch(api("/api/server-info")).then(r => r.json()).then(console.log);
fetch(api("/api/trades")).then(r => r.json()).then(d => console.log("Trades:", d.trades?.length));
```

---

## Still Not Working?

1. **Cloud logs:** `ssh root@150.241.244.130 "journalctl -u lab-trading-dashboard -n 50 --no-pager"`
2. **Direct API (no frontend):** `curl http://150.241.244.130:10000/api/trades` from your laptop — should return JSON if firewall allows.
