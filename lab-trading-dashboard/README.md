# Lab Trading Dashboard

React + Vite frontend and Node API for the trading dashboard. **The app runs only on your cloud server:** the Node.js server (`server.js`) runs on the cloud — no Render, no Vercel. GitHub holds only code; secrets stay on the cloud.

---

## Repo layout (GitHub = code, cloud = run + secrets)

| Where        | What |
|-------------|------|
| **GitHub**  | Frontend source (`src/`), server **template** (`server/server.example.js`), build config, deploy scripts. No secrets, no `server.js`, no `.env`. |
| **Cloud server** | Runs the app: Node server (`server.js` from `server.example.js`) + static frontend (`dist/`). **Secrets only here:** `/etc/lab-trading-dashboard.env` (e.g. `DATABASE_URL`, `PORT`). Never committed. |

- `server/server.js` is **not in Git** (in `.gitignore`). On the cloud it is created from `server/server.example.js` on each deploy so the server always runs the latest code; credentials are read from the env file only.
- To deploy: push code to GitHub, then either run the deploy on the cloud (e.g. GitHub Actions or `./deploy.sh` on the server) or build locally and upload with `./scripts/upload-dist.sh`.

---

## Quick start (local dev)

```bash
npm install
npm run dev
```

API in dev: proxy to `http://localhost:10000` (run the server separately if needed).

---

## Deploy to your cloud (server runs on your cloud only)

1. **One-time server setup**  
   On the cloud server, clone the repo and run setup (see `docs/DEPLOY_DASHBOARD_UBUNTU.md` or `scripts/setup-server-once.sh`). This creates `/etc/lab-trading-dashboard.env`; you add DB and other secrets there only.

2. **Secrets on the cloud only**  
   Edit on the server:
   ```bash
   sudo nano /etc/lab-trading-dashboard.env
   ```
   Add at least:
   - `PORT=10000` (or your port)
   - `DATABASE_URL=postgres://...` or `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` for your Postgres.

3. **Deploy updates**  
   - **From GitHub:** Push to `main`; if GitHub Actions is configured, it will SSH to the server and run `./deploy.sh` (git pull, build, copy `server.example.js` → `server.js`, restart).  
   - **From your machine:** Run `./scripts/upload-dist.sh` (uses `DEPLOY_HOST`/`DEPLOY_PASSWORD` from local `.env` to upload `dist/` and server template, then restart on the cloud).

---

## Scripts

| Script | Purpose |
|--------|---------|
| `./scripts/upload-dist.sh` | Build frontend and upload `dist/` + server template to cloud; restart service. Needs `.env` with `DEPLOY_HOST` (and optionally `DEPLOY_PASSWORD`). |
| `./deploy.sh` | Run on the **cloud server** (or via SSH in CI): git pull, build, copy `server.example.js` → `server.js`, restart. |
| `./scripts/setup-server-once.sh` | One-time cloud server setup: Node, clone repo, build, create `/etc/lab-trading-dashboard.env`, systemd service. |

---

## Env files

- **Local (optional):** `.env` — for `upload-dist.sh` only (`DEPLOY_HOST`, `DEPLOY_PASSWORD`). Do not commit; see `.env.deploy.example`.
- **Cloud only:** `/etc/lab-trading-dashboard.env` — `PORT`, `DATABASE_URL` or `DB_*`. Loaded by the Node server; never in Git.

---

## Tech

- [React](https://react.dev/) + [Vite](https://vitejs.dev/)
- Node (Express) API in `server/`; template `server.example.js`, actual `server.js` generated on deploy.
