# Reference: Changes made for Loveleet/lab_live (and for new repos)

Use this when cloning or creating a new repo (e.g. from lab_anish or another copy) so the same behavior works. Replace `lab_anish` → new repo name and `lab_live` → new repo name where applicable.

---

## 1. Repo and URL renames (old → new)

- **Repo:** `Loveleet/lab_anish` → `Loveleet/lab_live`
- **Pages URL:** `https://loveleet.github.io/lab_anish/` → `https://loveleet.github.io/lab_live/`

**Files to search/replace:**

| File | What to change |
|------|----------------|
| `scripts/update-github-secret-from-tunnel.sh` | Default `GITHUB_REPO`, comments |
| `scripts/run-tunnel-from-laptop.sh` | Repo and Pages URLs in comments and echo |
| `scripts/run-setup-on-cloud.sh` | `REPO_URL` default and comment |
| `scripts/install-tunnel-service-on-cloud.sh` | Echo with repo URL |
| `scripts/start-https-tunnel-for-pages.sh` | Comment (lab_anish → lab_live) |
| `.env.deploy.example` | `REPO_URL=...` |
| `docs/*.md` (GITHUB_PAGES_*, PAGES_404_FIX, ADD_WORKFLOW, FRONTEND_GITHUB_*, RESTART_CHECK) | All repo and Pages URLs |
| `vite.config.js` | Comment only: example path lab_anish → lab_live |
| Repo root `.env.example` | `REPO_URL`, `GITHUB_REPO` for new repo |

---

## 2. Workflows at repo root (required)

GitHub Actions runs only `.github/workflows/` at the **repository root**. If the app lives in a subdir (e.g. `lab-trading-dashboard/`), workflows must still be at **repo root** and reference the subdir.

**Create:** `.github/workflows/deploy-frontend-pages.yml` (at repo root)

- `on`: push to main/lab_live, workflow_dispatch
- `permissions`: contents: write, pages: write, id-token: write
- Steps: checkout → setup node (cache with cache-dependency-path: lab-trading-dashboard/package-lock.json) → **working-directory: lab-trading-dashboard** → npm ci, npm run build with `VITE_API_BASE_URL`, `VITE_BASE_PATH: /${{ github.event.repository.name }}/`
- Step: write `lab-trading-dashboard/dist/api-config.json` from `secrets.API_BASE_URL`
- Step: copy `lab-trading-dashboard/dist/index.html` → `lab-trading-dashboard/dist/404.html` (SPA routes)
- Deploy: `publish_dir: lab-trading-dashboard/dist`, force_orphan: true

**Create:** `.github/workflows/update-api-config.yml` (at repo root)

- `on`: schedule `cron: '*/2 * * * *'`, workflow_dispatch with input `api_url` (optional string)
- Resolve URL: input `api_url` → `secrets.API_BASE_URL` → curl `http://150.241.244.130:10000/api/tunnel-url` (expects `{"tunnelUrl":"https://..."}`)
- Checkout gh-pages, write `api-config.json` with `{ "apiBaseUrl": "<resolved URL>" }`, commit and push if changed

**One-time GitHub Settings:**

- Settings → Actions → General → Workflow permissions: **Read and write permissions**
- Settings → Pages → Source: Deploy from a branch → Branch: **gh-pages**, Folder: **/ (root)**

---

## 3. Frontend: runtime API URL from api-config.json

**File:** `lab-trading-dashboard/src/config.js`

- `runtimeApiBaseUrl` (set when api-config loads)
- `getBuildTimeDefault()`: use `VITE_API_BASE_URL`, no raw IP over HTTPS, return "" on GitHub Pages when no URL
- `getApiBaseUrl()`: return `runtimeApiBaseUrl` if set, else `getBuildTimeDefault()`
- `loadRuntimeApiConfig()`: fetch `(BASE_URL)/api-config.json`, support both `apiBaseUrl` and `tunnelUrl`, set `runtimeApiBaseUrl`, dispatch `api-config-loaded` only when URL actually changed
- On GitHub Pages: call `loadRuntimeApiConfig()` on load and `setInterval(loadRuntimeApiConfig, 2 * 60 * 1000)` to pick up new tunnel URL without refresh
- Only treat api-config as “loaded” when URL is non-empty; log empty once to avoid console spam
- Export: `getApiBaseUrl`, `loadRuntimeApiConfig`, `api(path)`

**File:** `lab-trading-dashboard/src/main.jsx`

- `BrowserRouter basename={import.meta.env.BASE_URL?.replace(/\/$/, '') || ''}` so routes work under `/repo_name/` (e.g. `/lab_live/live-trade-view`)

**File:** `lab-trading-dashboard/src/App.jsx`

- Import `getApiBaseUrl`, `loadRuntimeApiConfig`
- State: `apiBaseForBanner` (for “API not configured” banner), `apiUnreachable` (for “API unreachable” banner)
- Listen for `api-config-loaded`: update `apiBaseForBanner`, call `refreshAllData()`
- All API fetches use `api(...)` or `getApiBaseUrl()` (no raw `API_BASE_URL` for requests)
- `refreshAllData`: skip requests when on github.io and `!getApiBaseUrl()`; on catch (e.g. ERR_NAME_NOT_RESOLVED), set `apiUnreachable`, call `loadRuntimeApiConfig()` then retry `refreshAllData()` after 4s
- On success in `refreshAllData`: `setApiUnreachable(false)`
- Banners: “API not configured” when on github.io and !apiBaseForBanner and !apiUnreachable; “API unreachable (tunnel URL may have changed)” when apiUnreachable, with refetch/retry and cloud instructions

---

## 4. Cloud: auto-update secret and trigger workflow after tunnel restart

**File:** `scripts/update-github-secret-from-tunnel.sh`

- Read tunnel URL from `/var/log/cloudflared-tunnel.log` (default), retry up to 12 times with 5s sleep
- Write URL to `/var/run/lab-tunnel-url`
- If `GH_TOKEN` set (from `/etc/lab-trading-dashboard.env`): `gh secret set API_BASE_URL --body "$URL" --repo "$REPO"`, then `gh workflow run "Update API config" --ref main --repo "$REPO" -f "api_url=$URL"`
- Optional: `GITHUB_REPO=Loveleet/lab_live` in env

**File:** `scripts/cron-tunnel-update.sh`

- Append one line to `/var/log/lab-tunnel-update.log`, then run `update-github-secret-from-tunnel.sh`

**File:** `scripts/install-cron-tunnel-update.sh`

- Crontab: `@reboot sleep 90 && /opt/apps/lab-trading-dashboard/scripts/cron-tunnel-update.sh`
- Crontab: `*/10 * * * * /opt/apps/lab-trading-dashboard/scripts/cron-tunnel-update.sh`

**File:** `scripts/fix-api-config-and-cloud.sh` (run from laptop once)

- Copy `update-github-secret-from-tunnel.sh`, `cron-tunnel-update.sh`, `install-cron-tunnel-update.sh` to cloud `/opt/apps/lab-trading-dashboard/scripts/`
- chmod +x, run `install-cron-tunnel-update.sh` on cloud

**On cloud (one-time):** `/etc/lab-trading-dashboard.env` with `GH_TOKEN=ghp_...` and `GITHUB_REPO=Loveleet/lab_live`, chmod 600.

---

## 5. Backend: tunnel URL endpoint (for workflow fallback)

**File:** `server/server.example.js` (or your server entry)

- `GET /api/tunnel-url`: read URL from `/var/run/lab-tunnel-url`, respond `{ "tunnelUrl": "https://..." }` (or null). The Update API config workflow can curl this when no input and no secret.

---

## 6. Docs and examples added

- `docs/SETUP_NEW_REPO.md`: full setup (Cursor prompt, one-time GitHub and cloud steps)
- `docs/RESTART_CHECK.md`: what to do after cloud/tunnel restart (tunnel URL, secret, redeploy, verify)
- `docs/PAGES_404_FIX.md`: 404 fix, 403 fix (Workflow permissions Read and write), link to Secrets
- `docs/CHANGES_REFERENCE_LAB_LIVE.md`: this file
- Repo root `.env.example`: `REPO_URL=...`, `GITHUB_REPO=...`

---

## 7. One-time setup checklist (for a new repo)

1. **Rename** all repo/Pages URLs in scripts and docs (section 1).
2. **Workflows** at repo root (section 2); ensure deploy builds from subdir and publishes subdir/dist, and update-api-config writes api-config.json on gh-pages.
3. **GitHub:** Settings → Actions → General → Read and write permissions; Settings → Pages → gh-pages branch, / (root).
4. **Secrets:** API_BASE_URL = current tunnel URL (or leave empty and let workflow use curl or manual run with api_url).
5. **Run** Deploy frontend to GitHub Pages once; run Update API config once (or wait for 2 min schedule).
6. **Cloud:** Run from laptop `./scripts/fix-api-config-and-cloud.sh`; on cloud set `GH_TOKEN` and `GITHUB_REPO` in `/etc/lab-trading-dashboard.env`.

---

## 8. Optional / already-done for lab_live

- **Windows path fix:** Renamed `ChartLibraryGrid.css:` → `ChartLibraryGrid.css` (no trailing colon).
- **Console:** Log page URL and API base (or setup link) once on GitHub Pages; log empty api-config once; log api-config fetch URL once.
- **Banner:** “API not configured” with direct links to Secrets and Deploy workflow; “API unreachable” with refetch/retry and cloud script hint.

---

## 9. Summary table

| Area | What |
|------|------|
| Repo/URL | lab_anish → lab_live (and Pages URL) everywhere in scripts/docs |
| Workflows | At repo root: deploy-frontend-pages.yml (build subdir, write api-config + 404.html, publish dist), update-api-config.yml (api_url input, secret, curl fallback, write api-config to gh-pages) |
| Frontend config | config.js: runtime api-config, getBuildTimeDefault, loadRuntimeApiConfig, poll 2 min, tunnelUrl support |
| Frontend app | App.jsx: apiBaseForBanner, apiUnreachable, api-config-loaded listener, all fetches via api()/getApiBaseUrl, 404.html + Router basename |
| Cloud | update-github-secret-from-tunnel.sh (12×5s retry, gh secret set + workflow run with api_url), cron-tunnel-update.sh, install-cron-tunnel-update.sh, fix-api-config-and-cloud.sh |
| GitHub one-time | Workflow permissions Read and write, Pages from gh-pages, secret API_BASE_URL |
| Cloud one-time | GH_TOKEN and GITHUB_REPO in /etc/lab-trading-dashboard.env, run fix-api-config-and-cloud.sh from laptop |

Use this as reference when creating or adapting a new repo.
