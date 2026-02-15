# Skip Cloudflare & Fix Whole Workflow — Steps Checklist

This checklist tracks the steps from **SECURITY_AND_SECRETS_PLAN.md**. Mark each item when done.

---

## Step 1: Secrets file — ✅ DONE

- [x] **1a.** One secrets file: `secrets.env` (local) and `/etc/lab-trading-dashboard.secrets.env` (cloud). Never in Git.
- [x] **1b.** `server.js` loads secrets at startup (tries `SECRETS_FILE`, `server/secrets.env`, `../secrets.env`, `/etc/lab-trading-dashboard.secrets.env`).
- [x] **1c.** `secrets.env.example` in Git; `secrets.env` in `.gitignore`.
- [x] **1d.** On cloud: created `/etc/lab-trading-dashboard.secrets.env` with DB_* and restarted service. Logs show `[secrets] Loaded from /etc/lab-trading-dashboard.secrets.env` and DB connected.

---

## Step 2: Auth on all APIs — ✅ DONE

- [x] **2a.** Auth middleware `requireAuth` protects all `/api/*` routes (except `/api/health`, which is defined before the middleware).
- [x] **2b.** Allowlist: `POST /auth/login`, `POST /auth/logout`, `GET /api/health` (no auth). Everything else under `/api` requires session.
- [x] **2c.** `/api/set-log-path` moved after `requireAuth` so it is protected.
- [x] **2d.** Comment in `server.js`: "login only from DB (users table + crypt); no hardcoded credentials."
- [x] **2e.** Frontend: `apiFetch` dispatches `lab-unauthorized` on 401; App.jsx listens and sets logged out.

---

## Step 3: Remove Cloudflare — ✅ DONE

- [x] **3a.** **config.js:** Use fixed API URL only. Removed 2-minute refetch of api-config.json; load once on startup. All comments say "cloud URL" / "fixed API URL", not "tunnel".
- [x] **3b.** **App.jsx:** API unreachable and "API not configured for GitHub Pages" messages updated — no Cloudflare/tunnel wording; instructions use cloud URL (e.g. `http://150.241.244.130:10000`).
- [x] **3c.** **GitHub Actions:**  
  - `deploy-frontend-pages.yml`: comments say "cloud URL", not "tunnel".  
  - `update-api-config.yml`: no longer calls `/api/tunnel-url`; URL from input or secret `API_BASE_URL` only.
- [x] **3d.** **SingleTradeLiveView.jsx:** Error message updated to "set API_BASE_URL and redeploy".
- [x] **3e.** **Cloud server:** Stopped/disabled `cloudflared-tunnel` service; removed tunnel cron entries (`@reboot` and `*/10 * * * *` for `cron-tunnel-update.sh`).
- [ ] **3f.** *(Optional)* Delete unused tunnel scripts from repo: `update-github-secret-from-tunnel.sh`, `start-https-tunnel-for-pages.sh`, `run-tunnel-from-laptop.sh`, `install-tunnel-service-on-cloud.sh`, `cloudflared-tunnel.service`, `cron-tunnel-update.sh` (if present).

---

## Step 4: Nginx on the cloud (HTTPS) — ⬜ TO DO

- [ ] **4a.** **DNS:** Point a domain (e.g. `lab.yourdomain.com`) to cloud IP `150.241.244.130` (A record). Verify with `ping lab.yourdomain.com`.
- [ ] **4b.** **Install nginx + certbot on cloud:**  
  `sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx`
- [ ] **4c.** **Nginx config:** Add a server block that proxies `/`, `/api`, `/auth` to `http://127.0.0.1:10000`. Use the existing example in `docs/nginx-lab-trading.conf`; adjust `server_name` to your domain.
- [ ] **4d.** **HTTPS cert:** Run `sudo certbot --nginx -d lab.yourdomain.com` (use your actual domain). Certbot configures SSL and auto-renewal.
- [ ] **4e.** **Firewall:** Allow 80 and 443. Optionally restrict port 10000 to localhost so all traffic goes through nginx.
- [ ] **4f.** **Frontend config:** Set `VITE_API_BASE_URL=https://lab.yourdomain.com` for builds that hit this backend (or set GitHub secret `API_BASE_URL` to `https://lab.yourdomain.com` for Pages).
- [ ] **4g.** **CORS:** In `server.js` `allowedOrigins`, add `https://lab.yourdomain.com` (and keep `http://localhost:5173` for local dev).

---

## Step 5: Confirm login from DB only — ✅ DONE

- [x] **5a.** No code path bypasses DB login. Comment added in `server.js`: "login only from DB (users table + crypt); no hardcoded credentials."

---

## Step 6: Docs — ✅ DONE

- [x] **6a.** Updated **AUTH_SETUP** (removed `/api/tunnel-url` from allowlist), **ARCHITECTURE_AND_FLOW** (secrets path → `secrets.env` / `/etc/lab-trading-dashboard.secrets.env`).
- [x] **6b.** Updated **DEBUG_GITHUB_PAGES**, **GITHUB_PAGES_WORK_WITH_DATA**, **CLOUD_UPDATE_FOR_GITHUB_PAGES** to use fixed API URL and cloud IP/domain, no Cloudflare tunnel.

---

## Summary

| Step | Status   | Description |
|------|----------|-------------|
| 1    | ✅ Done  | Secrets file (one file, not in Git; loaded at startup on cloud) |
| 2    | ✅ Done  | Auth on all APIs (requireAuth, 401 → logout, /api/set-log-path protected) |
| 3    | ✅ Done  | Remove Cloudflare (fixed API URL, no tunnel, cron removed on server) |
| 4    | ⬜ To do | Nginx on cloud (HTTPS: domain → nginx → Node, certbot, CORS) |
| 5    | ✅ Done  | Confirm login from DB only (comment in code) |
| 6    | ✅ Done  | Update docs (no tunnel wording; cloud IP/domain) |

---

*Last updated: after Step 6 (docs updated).*
