# Cloud-only setup: GitHub = code, secrets on cloud

The app is designed to run **only on your cloud server**. The Node.js server (server.js) runs on the cloud — no third-party app hosting. Frontend and server template live in GitHub; the cloud runs the server and holds all secrets.

---

## What lives where

| Location | Contents |
|----------|----------|
| **GitHub repo** | Frontend source (`src/`), `server/server.example.js` (template, no credentials), build and deploy scripts. No `server.js`, no `.env`, no DB URLs or passwords. |
| **Cloud server** | Running app: Node server (`server.js` created from `server.example.js`) + built frontend (`dist/`). Secrets only in `/etc/lab-trading-dashboard.env`. |

---

## One-time: set up the cloud server

1. Clone the repo on the server (or use `scripts/setup-server-once.sh` with `REPO_URL`).
2. The setup creates `/etc/lab-trading-dashboard.env`. Put **all secrets there**:
   ```bash
   sudo nano /etc/lab-trading-dashboard.env
   ```
   Example:
   ```bash
   PORT=10000
   DATABASE_URL=postgres://user:password@your-db-host:5432/labdb2
   ```
   Or use `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` if you prefer.
3. Setup script copies `server.example.js` → `server.js` and starts the systemd service. After that, every deploy refreshes `server.js` from the template so the server always runs the code from Git; secrets stay in the env file.

---

## Deploying updates (easy upload from code)

**Option A – Push to GitHub, deploy on server**

- Configure GitHub Actions (see `.github/workflows/deploy.yml`) with `SSH_HOST`, `SSH_USER`, `SSH_KEY` so that on push to `main` it SSHs to the cloud and runs `./deploy.sh`.
- `deploy.sh` does: `git pull` → `npm ci` → `npm run build` → copy `server.example.js` → `server.js` → restart.

**Option B – Build locally, upload to cloud**

- On your machine, add to `.env`: `DEPLOY_HOST=root@YOUR_CLOUD_IP`, optionally `DEPLOY_PASSWORD=...`.
- Run:
  ```bash
  ./scripts/upload-dist.sh
  ```
  This builds the frontend, uploads `dist/` and `server/server.example.js` (as `server.js`) to the cloud, and restarts the service.

---

## Secrets checklist (cloud only)

- Never commit `server/server.js` or `.env` (they are in `.gitignore`).
- On the cloud, only `/etc/lab-trading-dashboard.env` should hold:
  - `PORT`
  - `DATABASE_URL` or `DB_HOST` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`
  - Any other env vars the server needs

The server reads this file on startup (and systemd can load it via `EnvironmentFile`). No secrets in the repo.
