# Auto-sync: Push to GitHub → Deploy to Cloud

Once set up, **every push to your configured branch** (e.g. `main` or `lab_live`) will automatically deploy to your cloud server (150.241.244.130). No need to run `upload-dist.sh` manually.

**Using a different branch:** Edit the workflow files and change the `branches` list. In `.github/workflows/deploy.yml` and `.github/workflows/deploy-frontend-pages.yml`, set e.g. `branches: [main, lab_live]` or only `branches: [lab_live]` so pushes to that branch trigger the deploy.

---

## Step 1: Create an SSH key for GitHub Actions (one-time)

On your **laptop**, open a terminal and run:

```bash
# Create a key (no passphrase so GitHub can use it non-interactively)
ssh-keygen -t ed25519 -f ~/.ssh/lab_deploy_key -N "" -C "github-actions-deploy"
```

This creates:

- **Private key:** `~/.ssh/lab_deploy_key` → you will put this in GitHub Secrets.
- **Public key:** `~/.ssh/lab_deploy_key.pub` → you will add this to the cloud server.

---

## Step 2: Add the public key to the cloud server

The cloud server must allow GitHub to SSH in using that key. From your **laptop** (in the repo root, with `.env` containing `DEPLOY_HOST` and `DEPLOY_PASSWORD`):

```bash
# From repo root, load .env
cd /path/to/lab-trading-dashboard
set -a && source .env && set +a

# Append the public key to root's authorized_keys on the cloud
SSHPASS="$DEPLOY_PASSWORD" sshpass -e ssh -o StrictHostKeyChecking=no "$DEPLOY_HOST" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$(cat ~/.ssh/lab_deploy_key.pub)' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo 'Key added.'"
```

If you prefer to do it manually: SSH into the cloud as root, then run:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
# Paste the contents of ~/.ssh/lab_deploy_key.pub (from your laptop) into:
nano ~/.ssh/authorized_keys
# Save, then:
chmod 600 ~/.ssh/authorized_keys
```

---

## Step 3: Add GitHub Secrets

1. Open your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** and add these:

| Name         | Value                     | Required |
|--------------|---------------------------|----------|
| `SSH_HOST`   | `150.241.244.130`          | Yes      |
| `SSH_USER`   | `root`                    | Yes      |
| `SSH_KEY`    | Contents of `~/.ssh/lab_deploy_key` (whole file, including `-----BEGIN ... KEY-----` and `-----END ... KEY-----`) | Yes |
| `SSH_PORT`   | `22`                      | No (default 22) |
| `SSH_APP_PATH` | `lab-trading-dashboard`  | No (default; use only if your app is in a different folder on the server) |

To copy the private key to the clipboard (macOS):

```bash
cat ~/.ssh/lab_deploy_key | pbcopy
```

Then paste into the `SSH_KEY` secret value.

---

## Step 4: Push to `main` and verify

1. Commit and push to the `main` branch:

   ```bash
   git add .
   git commit -m "Enable GitHub auto-deploy"
   git push origin main
   ```

2. On GitHub, open the **Actions** tab. You should see the **Deploy to Ubuntu** workflow run. Click it to see the log.

3. If it succeeds, your cloud app at http://150.241.244.130:10000 will be running the latest code. If it fails, check:
   - **"Error: /opt/apps/lab-trading-dashboard not found"** → Run the one-time server setup first (`scripts/setup-server-once.sh` or `docs/DEPLOY_DASHBOARD_UBUNTU.md`).
   - **Permission denied (publickey)** → Step 2: the public key is not in `root@150.241.244.130`’s `~/.ssh/authorized_keys`.
   - **Secrets not set** → Step 3: ensure `SSH_HOST`, `SSH_USER`, and `SSH_KEY` are set.

---

## Summary

| You do                         | What happens                                      |
|--------------------------------|---------------------------------------------------|
| Push to `main`                 | GitHub Actions runs and SSHs to your cloud        |
| On the cloud                   | `git pull`, `npm ci`, `npm run build`, copy `server.example.js` → `server.js`, restart service |
| Result                         | http://150.241.244.130:10000 serves the latest code |

Secrets (DB, FALLBACK_API_URL, etc.) stay only in `/etc/lab-trading-dashboard.env` on the cloud; they are never in GitHub. Each deploy only updates code and restarts the app.
