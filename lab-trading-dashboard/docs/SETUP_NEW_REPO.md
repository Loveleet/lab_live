# Set up this dashboard in a new GitHub repo (e.g. lab_live)

Use this when you create a **new repo** (e.g. `lab_live`) and want the same behavior: GitHub Pages frontend + auto-update of API URL after cloud restart.

---

## 1. What you need to decide

| Variable | Example | Meaning |
|----------|---------|--------|
| **GITHUB_OWNER** | `Loveleet` | Your GitHub username or org |
| **REPO_NAME** | `lab_live` | New repo name |
| **Pages URL** | `https://Loveleet.github.io/lab_live/` | `https://<GITHUB_OWNER>.github.io/<REPO_NAME>/` |

Full repo = `GITHUB_OWNER/REPO_NAME` (e.g. `Loveleet/lab_live`).

---

## 2. Cursor prompt (paste this in the NEW repo in Cursor)

**Easy copy-paste:** Open **`docs/CURSOR_PROMPT_NEW_REPO.txt`**, copy all, then in the **new** repo in Cursor paste into chat. Replace `Loveleet` and `lab_live` in the prompt with your actual owner and repo name if different.

Or copy the block below:

```
This codebase was copied from another repo. Adapt it for the GitHub repo Loveleet/lab_live.

Do the following:

1) Replace all references to the OLD repo and OLD Pages URL with the new one:
   - Old repo: Loveleet/lab_anish  →  New repo: Loveleet/lab_live
   - Old Pages URL: https://loveleet.github.io/lab_anish/  →  New: https://loveleet.github.io/lab_live/
   (Use the same GitHub owner and new repo name everywhere.)

2) Files to update (search and replace in each):
   - scripts/update-github-secret-from-tunnel.sh: GITHUB_REPO default and comment (Loveleet/lab_anish → Loveleet/lab_live)
   - scripts/run-tunnel-from-laptop.sh: repo and Pages URLs
   - scripts/run-setup-on-cloud.sh: REPO_URL default
   - scripts/install-tunnel-service-on-cloud.sh: repo URL in echo
   - scripts/fix-api-config-and-cloud.sh: Pages URL in echo
   - scripts/start-https-tunnel-for-pages.sh: comment with lab_anish → lab_live
   - .env.deploy.example: REPO_URL
   - docs/RESTART_CHECK.md: all github.com/.../lab_anish and loveleet.github.io/lab_anish
   - docs/GITHUB_PAGES_WORK_WITH_DATA.md: repo and Pages URLs
   - docs/GITHUB_PAGES_HTTPS_API.md: Pages URL
   - docs/PAGES_404_FIX.md: Pages URL and repo
   - docs/ADD_WORKFLOW_TO_GITHUB.md: repo URL and examples
   - docs/FRONTEND_GITHUB_BACKEND_CLOUD.md: Pages URL example
   - Any other docs or scripts that mention lab_anish or the old repo/URL

3) vite.config.js: update the comment only (example path lab_anish → lab_live). Do not change the logic; base path is set by the deploy workflow from repository.name.

4) Workflows: .github/workflows/update-api-config.yml and deploy-frontend-pages.yml — no repo name is hardcoded (they use the current repo). Ensure both exist and update-api-config runs every 2 min (cron: '*/2 * * * *').

5) Add a repo root .env.example or note: REPO_URL=https://github.com/Loveleet/lab_live.git and for cloud scripts GITHUB_REPO=Loveleet/lab_live.

After you finish, list the files you changed and the one-time GitHub and cloud steps from docs/SETUP_NEW_REPO.md (sections 3 and 4).
```

---

## 3. One-time GitHub setup (in the new repo)

Do these in **GitHub** for `GITHUB_OWNER/REPO_NAME`:

1. **Push code**  
   Push the adapted code to `main` (and optionally `lab_live`). Ensure `.github/workflows/` is on the **default branch** (usually `main`) so Actions sees the workflows.

2. **Enable Pages**  
   - **Settings** → **Pages**  
   - Source: **Deploy from a branch**  
   - Branch: **gh-pages**  
   - Folder: **/ (root)**  
   - Save. The first deploy will run when the "Deploy frontend to GitHub Pages" workflow runs and pushes to `gh-pages`.

3. **Workflow permissions**  
   - **Settings** → **Actions** → **General**  
   - Under **Workflow permissions**, select **Read and write permissions** (so the deploy workflow can push to `gh-pages`). Save.

4. **Secrets (Actions)**  
   - **Settings** → **Secrets and variables** → **Actions**  
   - Add **API_BASE_URL**: your current Cloudflare tunnel URL (e.g. `https://xxx.trycloudflare.com`).  
   - Used as build-time default by the deploy workflow.

5. **Run deploy once**  
   - **Actions** → **Deploy frontend to GitHub Pages** → **Run workflow** (branch: main).  
   - After it finishes, open `https://<GITHUB_OWNER>.github.io/<REPO_NAME>/` and hard-refresh.

6. **Optional: run Update API config once**  
   - **Actions** → **Update API config** → **Run workflow**  
   - (This workflow runs every 2 min on schedule; you can add steps to refresh config if needed.)

---

## 4. One-time cloud setup (so it auto-updates after restart)

On the **cloud server** (same one that runs the API and tunnel):

1. **Scripts and cron**  
   From your laptop (in the new repo), with `.env` containing `DEPLOY_HOST` and `DEPLOY_PASSWORD`:
   ```bash
   cd /path/to/repo/lab-trading-dashboard   # or repo root if scripts are at root
   ./scripts/fix-api-config-and-cloud.sh
   ```
   This copies the update scripts to the cloud and installs crontab (@reboot + every 10 min).

2. **Optional: instant update after reboot**  
   On the cloud, create `/etc/lab-trading-dashboard.env` with a GitHub token so the cloud can trigger the workflow as soon as the tunnel is up:
   ```bash
   sudo bash -c 'echo "GH_TOKEN=ghp_YOUR_PAT" >> /etc/lab-trading-dashboard.env'
   sudo bash -c 'echo "GITHUB_REPO=Loveleet/lab_live" >> /etc/lab-trading-dashboard.env'
   sudo chmod 600 /etc/lab-trading-dashboard.env
   ```
   Use a Personal Access Token with **repo** and **workflow** scope for the new repo. If you skip this, the **scheduled** workflow (every 2 min) or the cron from step 1 will still update when the cloud is reachable.

3. **Verify**  
   After a cloud restart, wait 2–4 minutes, then hard-refresh `https://Loveleet.github.io/lab_live/`. Check logs on cloud: `ssh root@YOUR_CLOUD_IP 'tail -30 /var/log/lab-tunnel-update.log'`.

---

## 5. Summary

| Step | Where | What |
|------|--------|------|
| Replace repo/URL in code and docs | This repo (or new repo with Cursor) | All mentions of old repo and old Pages URL → new |
| Push to new repo | Git | Default branch has .github/workflows |
| Pages + branch gh-pages | GitHub Settings | So the site is at github.io/REPO_NAME |
| Workflow permissions Read and write | GitHub Settings → Actions → General | So deploy can push to gh-pages |
| API_BASE_URL secret | GitHub Secrets | Current tunnel URL (optional; workflow/cron can update) |
| Deploy workflow run once | GitHub Actions | Creates gh-pages and site |
| fix-api-config-and-cloud.sh | Laptop → cloud | Scripts + cron on cloud |
| GH_TOKEN + GITHUB_REPO (optional) | Cloud /etc/lab-trading-dashboard.env | Instant update after reboot |

After this, the new repo will behave like the old one: Pages URL loads the dashboard, and within ~2 minutes of a cloud restart the API URL on Pages is updated automatically (or immediately if GH_TOKEN is set on the cloud).
