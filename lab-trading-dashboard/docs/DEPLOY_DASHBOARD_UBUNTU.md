# Deploy lab-trading-dashboard to Ubuntu VM

One-time server setup, then every push to `main` deploys via GitHub Actions (SSH).

---

## 1. Info you need

| Item | Example | Your value |
|------|---------|------------|
| **Repo URL** | `https://github.com/youruser/lab-trading-dashboard` | |
| **Server IP** | `203.0.113.50` | |
| **SSH username** | `ubuntu` | |
| **Repo dir on server** | `lab-trading-dashboard` (same as repo name) | |

---

## 2. One-time server setup (Ubuntu 22.04 / 24.04)

SSH in: `ssh YOUR_SSH_USER@YOUR_SERVER_IP`, then run the blocks below.

### 2.1 Install Node.js 20 and git

```bash
sudo apt-get update
sudo apt-get install -y git
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v
npm -v
```

### 2.2 Clone repo

```bash
sudo mkdir -p /opt/apps
sudo chown "$USER:$USER" /opt/apps
cd /opt/apps
git clone https://github.com/YOUR_USER/lab-trading-dashboard.git
cd lab-trading-dashboard
```

Replace the clone URL with your repo URL.

### 2.3 Build and install deps

```bash
cd /opt/apps/lab-trading-dashboard
npm ci
npm run build
cd server && npm ci && cd ..
```

### 2.4 Optional: env file for server (PORT, DB, etc.)

If your server needs `PORT`, database URL, or other env vars:

```bash
sudo tee /etc/lab-trading-dashboard.env << 'EOF'
PORT=10000
# Add any vars your server/server.js reads from process.env
EOF
sudo chmod 600 /etc/lab-trading-dashboard.env
sudo chown root:root /etc/lab-trading-dashboard.env
```

Edit with real values: `sudo nano /etc/lab-trading-dashboard.env`.  
If you don’t need an env file, skip this and remove the `EnvironmentFile=` line from the systemd unit below.

### 2.5 Systemd service

Replace `ubuntu` with your SSH user if different:

```bash
sudo tee /etc/systemd/system/lab-trading-dashboard.service << 'EOF'
[Unit]
Description=Lab Trading Dashboard (Node API)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/apps/lab-trading-dashboard/server
EnvironmentFile=-/etc/lab-trading-dashboard.env
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

If you didn’t create `/etc/lab-trading-dashboard.env`, run:

```bash
sudo sed -i '/EnvironmentFile/d' /etc/systemd/system/lab-trading-dashboard.service
```

### 2.6 Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable lab-trading-dashboard
sudo systemctl start lab-trading-dashboard
sudo systemctl status lab-trading-dashboard
```

### 2.7 Make deploy script executable

```bash
chmod +x /opt/apps/lab-trading-dashboard/deploy.sh
```

---

## 3. GitHub Actions (auto-deploy on push)

### 3.1 Secrets

In the repo: **Settings → Secrets and variables → Actions**, add:

| Secret    | Value        |
|-----------|--------------|
| `SSH_HOST`| Server IP    |
| `SSH_USER`| SSH username |
| `SSH_KEY` | Full private key (PEM) for SSH |
| `SSH_PORT`| Optional; default `22` |

### 3.2 Deploy trigger

- Push to `main`, or
- **Actions → Deploy to Ubuntu → Run workflow**

The workflow SSHs into the server, runs `./deploy.sh` (git pull, npm ci, build, restart service).

---

## 4. Ops commands

| Task        | Command |
|------------|--------|
| Follow logs | `journalctl -u lab-trading-dashboard -f` |
| Last 100   | `journalctl -u lab-trading-dashboard -n 100` |
| Restart    | `sudo systemctl restart lab-trading-dashboard` |
| Status     | `sudo systemctl status lab-trading-dashboard` |

---

## 5. Serving the frontend (optional)

The systemd service runs only the **Node API** (`server/server.js`). To serve the built frontend (`dist/`) from the same VM:

- **Option A:** Configure the Express app to serve `../dist` as static (add that in `server.js` and redeploy).
- **Option B:** Use Nginx to serve `dist/` and proxy `/api` and other API paths to `http://127.0.0.1:10000`.

Example Nginx (if you use it):

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /opt/apps/lab-trading-dashboard/dist;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:10000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then `sudo nginx -t && sudo systemctl reload nginx`.
