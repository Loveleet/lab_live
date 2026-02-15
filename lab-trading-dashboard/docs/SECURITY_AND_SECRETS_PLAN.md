# Security & Secrets Implementation Plan

This document describes how to implement your requirements: DB-only login, one secrets file (not on GitHub), no Cloudflare, auth on all APIs, and keeping the server code on GitHub while secrets stay off.

---

## 1. Login always from database ✅ (already done)

- **Current state:** `POST /auth/login` uses the `users` table and PostgreSQL `crypt()` — no hardcoded users.
- **Action:** None. Just ensure no other code path bypasses this (e.g. no dev-only “skip auth” that could be left on in production).
- **Optional:** Add a short comment in server.js above `/auth/login`: “Login only from DB (users table + crypt); no hardcoded credentials.”

---

## 2. One file for all API keys, passwords, and secrets (not on GitHub)

**Idea:** A single file holds every secret. The app loads it at startup. The file is never committed.

**Suggested approach:**

| Item | Recommendation |
|------|----------------|
| **File name** | Use one name everywhere: **`secrets.env`** (or keep **`.env`** — already in .gitignore). |
| **Location** | **Local:** project root or `lab-trading-dashboard/secrets.env`. **Cloud:** `/etc/lab-trading-dashboard.secrets.env` (or re-use `/etc/lab-trading-dashboard.env`). |
| **Format** | Standard env: `KEY=value`, one per line. No spaces around `=`. Optional: support `export KEY=value` for sourcing in shell. |
| **In Git** | Only a **template** is in Git: `secrets.env.example` (or `.env.example`) with placeholder keys and no real values. Add `secrets.env` and `.env` to .gitignore (already there for `.env`). |
| **Loading** | **Node:** At the very top of `server.js`, before any other logic: load the file and set `process.env` (e.g. `dotenv` or a small custom loader that tries `./secrets.env`, `../secrets.env`, `/etc/lab-trading-dashboard.secrets.env`). **Python:** Same file path or an env var like `SECRETS_FILE`; load in `api_signals.py` before starting the app. |

**What goes in the file (examples):**

- `DATABASE_URL` or `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`
- `ACTION_PASSWORD` (for execute/end-trade/etc. — if you still want a separate “action” password)
- `PYTHON_SIGNALS_URL` (if Node calls Python; can be defaulted in code for local)
- Any API keys (e.g. Telegram, external services) used by server or Python
- `SESSION_SECRET` or cookie signing key if you add signed cookies later (optional)
- No Cloudflare tokens (you’re dropping Cloudflare)

**Better input:**  
Using a single `secrets.env` (or `.env`) that is **never** committed and is loaded in one place per process is a good, simple approach. No need for a secret manager unless you scale to multiple apps and rotation.

---

## 3. No Cloudflare — use cloud IP only

You have a fixed cloud IP; the app will talk to the backend at that IP (and optionally a domain). Cloudflare tunnel and related logic can be removed or disabled.

**Remove or simplify:**

| Where | What to do |
|-------|------------|
| **server.js** | Remove or comment out: `GET /api/tunnel-url`, `TUNNEL_URL_FILE`, `TUNNEL_LOG_PATHS`, `TUNNEL_URL_REGEX`, and any logic that reads cloudflared logs. Update comments that mention “Cloudflare tunnel” or “GitHub Pages via tunnel”. |
| **CORS** | Keep `allowedOrigins` but adjust: if the frontend is only ever at `http://150.241.244.130:10000` (or your domain), you can list only that and `http://localhost:5173` for local dev. Remove `https://loveleet.github.io` if you are no longer using GitHub Pages. |
| **Frontend config (config.js)** | Stop using `api-config.json` for a “tunnel URL”. Use a **fixed API base URL**: build-time env (e.g. `VITE_API_BASE_URL=http://150.241.244.130:10000` for cloud, or empty for same-origin). Remove or simplify `loadRuntimeApiConfig()` and any 2‑minute refetch of api-config. |
| **GitHub Actions** | If you no longer use GitHub Pages for this app: remove or disable workflows that deploy to Pages and that write `api-config.json` from a tunnel URL. If you still use Pages but with cloud IP: set `API_BASE_URL` (or equivalent) to `http://150.241.244.130:10000` (or your HTTPS URL) and stop any “tunnel URL” update step. |
| **Scripts** | `update-github-secret-from-tunnel.sh`, `cron-tunnel-update.sh`, `install-cron-tunnel-update.sh`, `start-https-tunnel-for-pages.sh` — no longer needed; can be removed or left unused. |
| **Docs** | Update DEBUG_GITHUB_PAGES, GITHUB_PAGES_WORK_WITH_DATA, CLOUD_UPDATE_FOR_GITHUB_PAGES, etc., to say “use cloud IP (or domain)” and remove Cloudflare/tunnel instructions. |

**Result:** One fixed backend URL (cloud IP or your domain). No tunnel discovery, no api-config.json for tunnel.

---

## 4. All API calls require authentication (no outsider access)

**Idea:** Every API endpoint (except a small allowlist) checks that the request is from a logged-in user. No valid session → 401; frontend redirects to login.

**Implementation:**

1. **Auth middleware (server.js)**  
   - Read session cookie (e.g. `lab_session`).  
   - If missing → `401 { error: "Not logged in" }`.  
   - If present: look up session in DB (sessions + users). If invalid or expired → clear cookie, `401`.  
   - If valid: attach `req.user = { id, email }` and call `next()`.

2. **Allowlist (no auth):**  
   - `POST /auth/login`  
   - `POST /auth/logout`  
   - `GET /api/health` (so load balancers stay happy; optional)  
   - Optionally `GET /api/server-info` if you want a public “is the server up?” page; otherwise protect it.

3. **Protect everything else:**  
   - Apply the auth middleware to all routes under `/api/*` and any other sensitive path.  
   - E.g. `app.use("/api", authMiddleware)` and then explicitly allowlist the few that must be public:  
     - Either: use a separate router for public API routes, or  
     - Or: define auth middleware and apply it after the allowlisted routes so only the allowlist is excluded.

4. **Frontend:**  
   - Already sends `credentials: "include"` so the session cookie is sent.  
   - On 401: clear local state and redirect to login (or show “Session expired, please log in again”).

**Better input:**  
- Keep the allowlist small. Prefer “everything is protected except login, logout, and health.”  
- Optionally add rate limiting on `POST /auth/login` (e.g. by IP or email) to reduce brute force.

---

## 5. Server file on GitHub, secrets in the separate file

**Idea:** Server code lives in the repo; secrets never do. The server reads secrets from the single file at startup.

**Approach (recommended):**

- **In Git:** `server.js` and all app code. A template file like `secrets.env.example` with key names and placeholders (e.g. `DB_PASSWORD=your_password_here`).  
- **Not in Git:** `secrets.env` (and `.env` if you use that name). Add both to `.gitignore`.  
- **On the server (cloud):** Create `secrets.env` (or use `/etc/lab-trading-dashboard.secrets.env`) with real values; set permissions e.g. `chmod 600`; point the process to it (e.g. `SECRETS_FILE=/etc/lab-trading-dashboard.secrets.env` or have the server try that path when running as the app user).  
- **Loading:** At the very start of `server.js`, before creating the DB pool or reading any secret, load the chosen file and set `process.env`. No secrets in source code; no secrets in Git.

This is the standard, secure approach. A “better” alternative would be a proper secret manager (e.g. HashiCorp Vault, cloud provider secrets); for a single app and one server, one file is usually enough.

---

## 6. Nginx on the cloud (HTTPS)

**Why:** So traffic (including login cookies and API calls) is encrypted. Browsers treat HTTPS as required for secure cookies in production.

**Assumptions:** You have (or will have) a **domain name** pointing to your cloud IP (e.g. `lab.yourdomain.com` → `150.241.244.130`). Without a domain, Let's Encrypt cannot issue a certificate (it needs a hostname to validate).

**Plan:**

| Step | What to do |
|------|------------|
| **1. Domain** | Point a DNS A record (e.g. `lab.yourdomain.com`) to your cloud server IP `150.241.244.130`. Wait for DNS to propagate. |
| **2. Install nginx + certbot** | On the cloud (Ubuntu): `sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx`. |
| **3. Nginx as reverse proxy** | Configure nginx to proxy to your Node app. Example: `proxy_pass http://127.0.0.1:10000` for `/` and `/api` and `/auth`. Node keeps listening on `localhost:10000`; nginx listens on 80/443. |
| **4. Get HTTPS cert** | Run `sudo certbot --nginx -d lab.yourdomain.com`. Certbot configures nginx for HTTPS and auto-renewal. |
| **5. Firewall** | Allow 80 and 443; optionally close direct access to port 10000 from the internet (only localhost) so all traffic goes through nginx. |
| **6. App config** | Set `NODE_ENV=production` and in `secrets.env`: no change needed for Node. Frontend build: use `VITE_API_BASE_URL=https://lab.yourdomain.com` so the app calls your API over HTTPS. |
| **7. CORS** | In server.js `allowedOrigins`, add `https://lab.yourdomain.com` (and keep `http://localhost:5173` for local dev). |

**Optional:** Serve the frontend static files from nginx too (e.g. build with `npm run build`, upload `dist/` to the server, nginx serves it at `https://lab.yourdomain.com` and proxies `/api` and `/auth` to Node). Then you have one URL for both UI and API.

**Result:** Users and the frontend talk to `https://lab.yourdomain.com`; nginx terminates SSL and forwards to Node. Cookies are secure; no Cloudflare needed.

---

## Suggested order of implementation

1. **Secrets file**  
   - Add `secrets.env.example` (or document in existing `.env.example`).  
   - Implement loading in `server.js` (and Python if needed).  
   - Move all sensitive config (DB, action password, API keys) to env vars read from that file.  
   - Ensure `.gitignore` excludes `secrets.env` and `.env`.

2. **Auth on all APIs**  
   - Add session-check middleware.  
   - Apply to `/api/*` with a small allowlist (login, logout, health).  
   - Frontend: handle 401 and redirect to login.

3. **Remove Cloudflare**  
   - Remove tunnel endpoint and related code.  
   - Simplify frontend API base URL to cloud IP or domain.  
   - Clean up workflows and scripts that depend on tunnel.

4. **Nginx on the cloud (HTTPS)**  
   - Point domain to cloud IP; install nginx + certbot; reverse proxy to Node (port 10000); run certbot for HTTPS; restrict port 10000 to localhost; set `VITE_API_BASE_URL=https://your-domain` and CORS.

5. **Confirm login from DB only**  
   - Quick review and a comment in code; no functional change if already correct.

6. **Docs**  
   - Update AUTH_SETUP, ARCHITECTURE, and any “tunnel/Cloudflare” docs to match the new setup.

---

## Summary

| Requirement | Approach |
|-------------|----------|
| Login from DB only | Already done; add a comment and avoid any bypass. |
| One file for keys/passwords, not on GitHub | Single `secrets.env` (or `.env`) in .gitignore; only `secrets.env.example` in Git; load at startup in server and Python. |
| No Cloudflare | Remove tunnel URL, api-config for tunnel, and related scripts; use fixed cloud IP or **domain + nginx**. |
| All API calls authenticated | Auth middleware on `/api/*` with allowlist (login, logout, health); 401 → frontend redirect to login. |
| Server on GitHub, secrets in file | Server code in repo; all secrets in one file loaded at startup; file not in Git. |
| **Nginx on cloud (HTTPS)** | Domain → cloud IP; nginx reverse proxy to Node; Let's Encrypt (certbot); traffic over HTTPS; cookies secure. |

If you want, next step can be concrete code changes: (1) secrets loading in `server.js` and `secrets.env.example`, (2) auth middleware and allowlist, (3) removal of Cloudflare-related code, (4) nginx config + certbot steps on the cloud.
