# Step 4: Nginx on the Cloud (HTTPS) — Step-by-step

Goal: Serve your **backend API** over **HTTPS** using a domain. Your **frontend** can stay on GitHub Pages (e.g. https://loveleet.github.io/lab_live/). This step is about giving the **cloud server** a domain and HTTPS so the API is at e.g. `https://api.yourdomain.com` instead of `http://150.241.244.130:10000`.

- **Frontend (UI):** https://loveleet.github.io/lab_live/ ← no change
- **Backend (API):** today = `http://150.241.244.130:10000` → after Step 4 = `https://your-domain.com` (a domain you point to `150.241.244.130`)

**Prerequisite:** A **domain or subdomain** (e.g. `api.yourdomain.com` or `lab-api.com`) with an **A record** pointing to your server IP `150.241.244.130`. This is **not** the GitHub Pages URL.

---

## 4a. Point your domain to the server

1. In your domain registrar or DNS provider (e.g. GoDaddy, Namecheap, Cloudflare DNS, etc.):
   - Add (or edit) an **A record**:
     - **Name/host:** `lab` (for `lab.yourdomain.com`) or `@` (for root) or the subdomain you want
     - **Value/Target:** `150.241.244.130`
     - **TTL:** 300 or default
2. Wait 2–10 minutes for DNS to propagate.
3. **Verify** (from your laptop or the server):
   ```bash
   ping lab.yourdomain.com
   ```
   You should see `150.241.244.130`. Replace `lab.yourdomain.com` with your actual hostname in all steps below.

---

## 4b. Install Nginx and Certbot on the cloud

SSH into the server, then run:

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

Check that nginx is running:

```bash
sudo systemctl status nginx
```

---

## 4c. Add Nginx config for your app

1. Create a config file (replace `lab.yourdomain.com` with your real domain):

   ```bash
   sudo nano /etc/nginx/sites-available/lab-trading
   ```

2. Paste this (change `server_name` to your domain):

   ```nginx
   server {
       listen 80;
       server_name lab.yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:10000;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. Save and exit (Ctrl+O, Enter, Ctrl+X in nano).

4. Enable the site and reload nginx:

   ```bash
   sudo ln -sf /etc/nginx/sites-available/lab-trading /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. **Test:** Open `http://lab.yourdomain.com` in a browser. You should see your app (or login page). It will be HTTP only until the next step.

---

## 4d. Get an HTTPS certificate with Certbot

Run (replace with your domain):

```bash
sudo certbot --nginx -d lab.yourdomain.com
```

- Enter your email when asked (for renewal notices).
- Agree to the terms.
- Choose whether to redirect HTTP → HTTPS (recommended: **Yes**).

Certbot will edit the nginx config to add SSL and redirect. Then:

```bash
sudo systemctl reload nginx
```

**Test:** Open `https://lab.yourdomain.com`. You should see the padlock and your app.

---

## 4e. Firewall (optional but recommended)

Allow HTTP and HTTPS; optionally block direct access to port 10000 from the internet:

```bash
# If ufw is used:
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
# Optional: allow only localhost to reach 10000 (nginx still can)
# You’d do this by not opening 10000 in the firewall; by default it’s often closed.
sudo ufw status
sudo ufw enable   # if you want to enable the firewall
```

---

## 4f. Use the domain in the frontend

So the dashboard calls the API at `https://lab.yourdomain.com`:

- **If you build and deploy from your machine or CI:**  
  Set `VITE_API_BASE_URL=https://lab.yourdomain.com` when building (env or `.env`), then deploy.
- **If you use GitHub Pages:**  
  In the repo: **Settings → Secrets and variables → Actions** → set **API_BASE_URL** to `https://lab.yourdomain.com` (no trailing slash). Then run the **Deploy frontend to GitHub Pages** workflow.

---

## 4g. Allow your domain in CORS (server)

The Node app must allow requests from `https://lab.yourdomain.com`. Add that origin in `server.js`:

1. Open `lab-trading-dashboard/server/server.js`.
2. Find the `allowedOrigins` array (near the top).
3. Add your HTTPS URL:

   ```javascript
   const allowedOrigins = [
     "http://localhost:5173",
     "http://localhost:5174",
     "http://localhost:10000",
     "http://150.241.244.130:10000",
     "https://loveleet.github.io",
     "https://lab.yourdomain.com",   // Your domain (HTTPS)
   ];
   ```

4. Save, then copy the updated `server.js` to the cloud and restart:

   ```bash
   # From your laptop (in the repo):
   ./scripts/copy-server-to-cloud.sh root 150.241.244.130 /root/lab-trading-dashboard
   ```

   On the server:

   ```bash
   sudo systemctl restart lab-trading-dashboard
   ```

---

## Checklist

- [ ] 4a. Domain A record → `150.241.244.130`; `ping` works
- [ ] 4b. `nginx` + `certbot` installed; nginx running
- [ ] 4c. Site config in `/etc/nginx/sites-available/lab-trading`; enabled; `http://yourdomain` works
- [ ] 4d. `certbot --nginx -d yourdomain`; `https://yourdomain` works
- [ ] 4e. Firewall allows 80, 443 (and 22)
- [ ] 4f. Frontend uses `https://yourdomain` (VITE_API_BASE_URL or API_BASE_URL secret)
- [ ] 4g. `allowedOrigins` in server.js includes `https://lab.yourdomain.com`; server restarted on cloud

After this, Step 4 is complete.
