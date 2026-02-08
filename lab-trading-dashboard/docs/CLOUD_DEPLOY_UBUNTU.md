# Deploy Python Trading Bot to Ubuntu (auto-update on push)

Run your bot 24/7 on an Ubuntu VM with auto-deploy when you push to `main`. Secrets stay only on the server.

---

## 1. Information needed (fill these first)

Before running any commands, have these ready:

| Item | Example | Your value |
|------|---------|------------|
| **Repo URL** | `https://github.com/youruser/trading-bot` | |
| **Server IP** | `203.0.113.50` | |
| **SSH username** | `ubuntu` or `root` | |
| **Bot entry file** | `main.py` (or `bot.py`, `run.py`) | |
| **Repo directory name on server** | `trading-bot` (often same as repo name) | |

**Conventions used below:**

- `REPO_URL` = your GitHub repo URL (HTTPS or SSH)
- `REPO_DIR` = directory name on server, e.g. `trading-bot` → full path `/opt/apps/trading-bot`
- `BOT_ENTRY` = entry file, e.g. `main.py`
- `SSH_USER` = SSH username
- `SERVER_IP` = server IP

---

## 2. Server setup (Ubuntu 22.04 / 24.04)

Run these on the server (SSH in first: `ssh SSH_USER@SERVER_IP`).

### 2.1 Install git and Python venv

```bash
sudo apt-get update
sudo apt-get install -y git python3-venv python3-pip
```

### 2.2 Create app directory and clone repo

```bash
sudo mkdir -p /opt/apps
sudo chown "$USER:$USER" /opt/apps
cd /opt/apps
git clone REPO_URL REPO_DIR
cd REPO_DIR
```

Replace `REPO_URL` and `REPO_DIR` (e.g. `git clone https://github.com/youruser/trading-bot.git trading-bot`).

### 2.3 Create venv and install dependencies

```bash
cd /opt/apps/REPO_DIR
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

### 2.4 Create env file for secrets (no real keys in repo)

```bash
sudo tee /etc/tradingbot.env << 'EOF'
# Binance API – set real values on server; never commit this file.
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
EOF
```

Edit and set real values:

```bash
sudo nano /etc/tradingbot.env
```

Lock permissions:

```bash
sudo chmod 600 /etc/tradingbot.env
sudo chown root:root /etc/tradingbot.env
```

### 2.5 Create systemd service

Replace `REPO_DIR` and `BOT_ENTRY` (e.g. `main.py`):

```bash
sudo tee /etc/systemd/system/tradingbot.service << 'EOF'
[Unit]
Description=Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/apps/REPO_DIR
EnvironmentFile=/etc/tradingbot.env
ExecStart=/opt/apps/REPO_DIR/.venv/bin/python -u BOT_ENTRY
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

**Fix placeholders:** run once (with your values):

```bash
sudo sed -i "s|REPO_DIR|trading-bot|g" /etc/systemd/system/tradingbot.service
sudo sed -i "s|BOT_ENTRY|main.py|g" /etc/systemd/system/tradingbot.service
```

If your user is not `ubuntu`, change `User=` and `Group=` in the service file.

### 2.6 Enable and start service

```bash
sudo systemctl daemon-reload
sudo systemctl enable tradingbot
sudo systemctl start tradingbot
sudo systemctl status tradingbot
```

---

## 3. Deploy script on server

Create `deploy.sh` in your **bot repo root** (so it’s in the clone on the server). The workflow runs it from `/opt/apps/<repo_name>/deploy.sh`.

**Content (copy-paste):** use the file `docs/deploy.sh` in this repo, or:

```bash
#!/usr/bin/env bash
# Copy to your bot repo root and to server at /opt/apps/<your-repo-dir>/deploy.sh
# On server: chmod +x deploy.sh

set -euo pipefail
cd "$(dirname "$0")"
git fetch origin main
git reset --hard origin/main
.venv/bin/pip install -q -r requirements.txt
sudo systemctl restart tradingbot
echo "Deploy done."
```

**On server after first clone:**

```bash
chmod +x /opt/apps/REPO_DIR/deploy.sh
```

If `deploy.sh` is not present, the workflow falls back to inline deploy commands (fetch, pip install, restart).

---

## 4. GitHub Actions workflow

Create in your **bot repo** (not this dashboard repo if different):

**File:** `.github/workflows/deploy.yml`

(See the file at repo root: `.github/workflows/deploy.yml` in this project, or copy the YAML below.)

**GitHub Secrets to add:**  
Repo → Settings → Secrets and variables → Actions:

| Secret    | Description                    |
|-----------|--------------------------------|
| `SSH_HOST`| Server IP                      |
| `SSH_USER`| SSH username                   |
| `SSH_PORT`| Optional, default `22`         |
| `SSH_KEY` | Private key (full content)     |

---

## 5. Safety

### .gitignore (bot repo)

Ensure these are in `.gitignore` so secrets are never committed:

```gitignore
# Env and secrets
.env
.env.*
*.env
!*.env.example
tradingbot.env
*secret*
*credentials*
```

### If you ever commit secrets

1. Rotate Binance API keys immediately in Binance → API Management (revoke old, create new).
2. Remove the secret from git history (e.g. `git filter-branch` or BFG Repo-Cleaner) and force-push.
3. Update `/etc/tradingbot.env` on the server with the new keys and restart: `sudo systemctl restart tradingbot`.

### Binance API hardening

- In Binance API settings: **Restrict access to trusted IPs only** and add your server’s public IP.
- **Disable withdrawals** for the API key if the bot does not need to withdraw.

---

## 6. Ops commands

| Task           | Command |
|----------------|--------|
| Follow logs    | `journalctl -u tradingbot -f` |
| Last 100 lines | `journalctl -u tradingbot -n 100` |
| Restart        | `sudo systemctl restart tradingbot` |
| Status         | `sudo systemctl status tradingbot` |
| Stop           | `sudo systemctl stop tradingbot` |
| Start          | `sudo systemctl start tradingbot` |

---

## 7. Optional: bot listens on a port (e.g. FastAPI)

If the bot exposes HTTP (e.g. FastAPI on `0.0.0.0:8000`):

- Binding to `0.0.0.0` makes it reachable on the server IP; restrict with a firewall (`ufw allow 8000`, then `ufw enable`).
- For HTTPS and a domain, put Nginx in front:

```nginx
# /etc/nginx/sites-available/tradingbot
server {
    listen 80;
    server_name your-domain.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then:

```bash
sudo ln -s /etc/nginx/sites-available/tradingbot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Use certbot for TLS if needed.
