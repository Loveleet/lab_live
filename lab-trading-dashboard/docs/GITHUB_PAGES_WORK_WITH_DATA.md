# Make GitHub Pages work with data

To have **https://loveleet.github.io/lab_live/** show real data (not just the UI), the frontend must call your **backend API**. Use a **fixed backend URL**: your cloud IP (e.g. `http://150.241.244.130:10000`) or your domain. No tunnel.

---

## Step 1: Backend must be reachable

Your Node API runs on the cloud at **http://150.241.244.130:10000** (or at an HTTPS domain if you set up nginx + certbot). From the internet:

- **Option A – Cloud IP:** Use `http://150.241.244.130:10000` as the API URL. Works as long as your server and firewall allow it.
- **Option B – Domain + HTTPS:** Point a domain to the cloud, set up nginx + certbot (see **docs/STEP_4_NGINX_HTTPS.md**), then use `https://your-domain.com` as the API URL.

---

## Step 2: Set the API URL in GitHub

1. Open **https://github.com/Loveleet/lab_live** → **Settings** → **Secrets and variables** → **Actions**.
2. Add or edit **API_BASE_URL**.
3. **Value:** your backend URL, e.g. `http://150.241.244.130:10000` (no trailing slash). If you have a domain with HTTPS, use that instead (e.g. `https://api.yourdomain.com`).
4. Save.

---

## Step 3: Redeploy the frontend

So the new build and api-config.json use this URL:

- **Actions** → **Deploy frontend to GitHub Pages** → **Run workflow** (branch: lab_live or main).

Wait for the workflow to finish.

---

## Step 4: Open the dashboard

Open **https://loveleet.github.io/lab_live/** and hard refresh (Ctrl+Shift+R / Cmd+Shift+R). Data should load from your backend.

---

## If the backend URL changes

If you change the backend (e.g. new IP or domain):

1. Update the **API_BASE_URL** secret in GitHub.
2. Run **Deploy frontend to GitHub Pages** again (or push a commit that triggers it).

---

## Troubleshooting

1. **api-config.json** – The frontend loads it from the deployed site. The deploy workflow writes it from **API_BASE_URL**. If the console shows "api-config.json not found", set the secret and run the deploy workflow again.
2. **CORS** – The cloud server must allow origin `https://loveleet.github.io` in `server.js` `allowedOrigins`. Deploy latest server to the cloud and restart.
3. **Database** – The cloud must use the **olab** database. Set **DB_NAME=olab** (and other DB_* if needed) in `/etc/lab-trading-dashboard.secrets.env` on the cloud. See **docs/CLOUD_UPDATE_FOR_GITHUB_PAGES.md**.
4. **Verify** – Open `http://150.241.244.130:10000/api/server-info` (or your domain). Should show `hasGitHubPagesOrigin: true` and `database: "olab"`. Then open `/api/trades` and confirm a non-empty `trades` array.
