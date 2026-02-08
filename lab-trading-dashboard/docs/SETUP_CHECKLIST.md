# Setup: Laptop → Cloud Ubuntu + GitHub (one-time)

Use this checklist to get your code running on the cloud and auto-deploying on push. **You share:** server IP, SSH user, GitHub repo URL. **You do:** push code, run one script on the server, add GitHub secrets.

---

## What you need (fill these)

| What | Example | Your value |
|------|---------|------------|
| **Server IP** | `203.0.113.50` | |
| **SSH user** | `ubuntu` | |
| **GitHub repo URL** | `https://github.com/youruser/lab-trading-dashboard` | |
| **Repo clone URL** | `https://github.com/youruser/lab-trading-dashboard.git` | (same + `.git`) |

---

## Step 1: Push your code to GitHub (from laptop)

Make sure this project is on GitHub and the branch you use is `main`.

```bash
cd /path/to/lab-trading-dashboard
git remote -v   # should show your GitHub repo
git push origin main
```

If the repo is **private**, the server will need to clone it. You can use:
- **HTTPS + Personal Access Token:** when the script runs `git clone`, it will ask for username (your GitHub user) and password (use a **PAT** with `repo` scope).
- Or create an **SSH deploy key** on the server and add the public key to the repo (Settings → Deploy keys).

---

## Step 2: One-time setup on the cloud (Ubuntu)

### 2.1 Copy the setup script to the server

From your **laptop** (in this repo):

```bash
cd "/Volumes/Loveleet /Work/Binance/lab_live/lab_live/lab-trading-dashboard"
scp scripts/setup-server-once.sh YOUR_SSH_USER@YOUR_SERVER_IP:/tmp/
```

Replace `YOUR_SSH_USER` and `YOUR_SERVER_IP` (e.g. `ubuntu@203.0.113.50`).

### 2.2 Run the script on the server

SSH in and run (replace the repo URL with yours):

```bash
ssh YOUR_SSH_USER@YOUR_SERVER_IP
```

Then on the **server**:

```bash
REPO_URL=https://github.com/YOUR_USER/lab-trading-dashboard.git /bin/bash /tmp/setup-server-once.sh
```

If your SSH user is not `ubuntu`, set it:

```bash
REPO_URL=https://github.com/YOUR_USER/lab-trading-dashboard.git RUN_AS_USER=ubuntu /bin/bash /tmp/setup-server-once.sh
```

- For a **private repo**, the script will run `git clone`; when prompted, use your GitHub username and a **Personal Access Token** (not your password).
- When it finishes, the API is running. Check: `curl http://localhost:10000` (on the server) or `curl http://YOUR_SERVER_IP:10000` from your laptop (if the VM firewall allows it).

---

## Step 3: GitHub Secrets (for auto-deploy on push)

So that every push to `main` deploys to the server, GitHub Actions needs to SSH into the server. Add these **secrets** in the repo:

**Repo → Settings → Secrets and variables → Actions → New repository secret**

### 3.1 Create an SSH key for GitHub Actions (on your laptop, one-time)

Run this **on your laptop** to generate a key **only for this deploy** (no passphrase so Actions can use it):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/lab_dashboard_deploy -N "" -C "github-actions-deploy"
```

Add the **public** key to the server so the key can log in:

```bash
ssh-copy-id -i ~/.ssh/lab_dashboard_deploy.pub YOUR_SSH_USER@YOUR_SERVER_IP
```

Test:

```bash
ssh -i ~/.ssh/lab_dashboard_deploy YOUR_SSH_USER@YOUR_SERVER_IP "echo OK"
```

### 3.2 Add these secrets in GitHub

In the repo: **Settings → Secrets and variables → Actions**, add:

| Name | Value | Notes |
|------|--------|--------|
| `SSH_HOST` | Your server IP | e.g. `203.0.113.50` |
| `SSH_USER` | SSH username | e.g. `ubuntu` |
| `SSH_KEY` | **Private** key content | See below |
| `SSH_PORT` | (optional) | Only if not `22` |

**For `SSH_KEY`:** paste the **entire** private key (one line or multiple lines, as in the file):

```bash
cat ~/.ssh/lab_dashboard_deploy
```

Copy the full output (including `-----BEGIN ... KEY-----` and `-----END ... KEY-----`) into the secret value.

---

## Step 4: Deploy (and future deploys)

- **First deploy** is already done by the setup script (code is cloned and running).
- **Later:** push to `main` from your laptop; the workflow will run and update the server.

Or from the laptop, deploy without pushing to GitHub:

```bash
export DEPLOY_HOST=YOUR_SSH_USER@YOUR_SERVER_IP
./scripts/deploy-to-server.sh
```

---

## Quick reference

| Task | Command |
|------|--------|
| **Logs on server** | `journalctl -u lab-trading-dashboard -f` |
| **Restart on server** | `sudo systemctl restart lab-trading-dashboard` |
| **Status on server** | `sudo systemctl status lab-trading-dashboard` |
| **Manual deploy from laptop** | `DEPLOY_HOST=user@ip ./scripts/deploy-to-server.sh` |

---

## If something goes wrong

- **Clone fails (private repo):** Use a Personal Access Token (HTTPS) or add the server’s SSH public key as a Deploy key in the repo.
- **Service won’t start:** Run `journalctl -u lab-trading-dashboard -n 50` and fix env or port (edit `/etc/lab-trading-dashboard.env` if needed).
- **GitHub Action fails:** Check that `SSH_HOST`, `SSH_USER`, and `SSH_KEY` are correct and that `ssh -i key USER@HOST` works from your laptop.
