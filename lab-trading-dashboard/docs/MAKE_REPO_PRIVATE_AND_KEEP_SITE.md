# Make the repo private and keep the website working

**Short answer:** On a **free** GitHub account, if you make the repo **private**, **GitHub Pages stops** for that repo. To keep the site working you either keep the repo public, upgrade GitHub, or host the site somewhere else.

Below is a **step-by-step guide** for each option.

---

## What happens when you make the repo private?

| Account type | GitHub Pages with private repo |
|--------------|---------------------------------|
| **Free**     | ❌ Not available — Pages only works for **public** repos. |
| **Pro / Team / Enterprise** | ✅ Available — you can publish Pages from a private repo. |

So on a **free** account, as soon as you set the repo to **Private**, the site at **https://loveleet.github.io/lab_live/** will stop being updated (and may show 404 or an old build).

---

## Option A: Keep the repo public (easiest)

If you want the website to keep working with **no change**:

1. Do **not** change the repo visibility.
2. Leave it **Public**.
3. The site at **https://loveleet.github.io/lab_live/** (and **clubinfotech.com** redirect) continues to work as now.

**If you want to hide code:** You can’t have both a free GitHub Pages site and a private repo. You’d need Option B or C.

---

## Option B: Make repo private + use GitHub Pro (Pages on private repo)

If you want the repo **private** and the site **still on GitHub Pages**:

### Step 1: Upgrade to GitHub Pro

1. Open **GitHub** → click your profile (top right) → **Settings**.
2. In the left sidebar, click **Billing and planning** → **Plans and usage**.
3. Under **GitHub Pro**, click **Upgrade** and complete payment.

### Step 2: Make the repo private

1. Open your repo: **https://github.com/Loveleet/lab_live**
2. Go to **Settings** (repo settings, not your account).
3. Scroll to the **Danger Zone** section.
4. Click **Change repository visibility**.
5. Choose **Make private** and confirm (type the repo name if asked).

### Step 3: Confirm GitHub Pages still works

1. In the same repo, go to **Settings** → **Pages**.
2. Source should still be **GitHub Actions** (or the branch you use for Pages).
3. After the next push/run of “Deploy frontend to GitHub Pages”, the site at **https://loveleet.github.io/lab_live/** will still update.

**Result:** Repo is private, site still works on GitHub Pages.

---

## Option C: Make repo private + host the site on your server (no GitHub Pro)

Here you make the repo **private** and serve the **same website** from your own server (e.g. **clubinfotech.com** or the cloud server), so you don’t need GitHub Pages.

### Step 1: Build the frontend locally (or in CI)

On your laptop (in the repo):

```bash
cd lab-trading-dashboard
npm ci
VITE_BASE_PATH=/ npm run build
```

The built files are in **`dist/`**.

### Step 2: Deploy `dist/` to your server

Copy the contents of `dist/` to your server, e.g. where nginx serves the site:

```bash
# Example: deploy to cloud server
rsync -avz --delete dist/ root@150.241.244.130:/var/www/lab-dashboard/
```

(Use your real path if different.)

### Step 3: Nginx: serve the site at clubinfotech.com (or a subdomain)

On the server, configure nginx so **clubinfotech.com** (or e.g. **app.clubinfotech.com**) serves the files from that folder instead of redirecting to GitHub:

- **Remove** (or don’t add) the redirect to `loveleet.github.io`.
- Set **root** (or **alias**) to `/var/www/lab-dashboard` (or wherever you put `dist/`).
- Restart nginx: `sudo nginx -t && sudo systemctl reload nginx`.

Now the “website” is your server, not GitHub Pages.

### Step 4: Make the repo private on GitHub

1. Repo **Settings** → **Danger Zone** → **Change repository visibility** → **Make private**.

### Step 5: Keep the site updated when you change code

- Either run **Step 1 + Step 2** manually when you update the frontend.
- Or use a **private CI** (e.g. GitHub Actions with repo access, or another CI) that builds and runs the same `rsync` (or your deploy script) so the server always has the latest build.

**Result:** Repo is private; website works from your server; **https://loveleet.github.io/lab_live/** is no longer used (you can turn off Pages in repo Settings → Pages).

---

## Summary

| Goal | What to do |
|------|------------|
| No change, site keeps working | **Option A** — leave repo public. |
| Repo private, site still on GitHub | **Option B** — upgrade to GitHub Pro, then make repo private. |
| Repo private, no GitHub Pro | **Option C** — make repo private, build frontend, deploy to your server and serve it there. |

---

## Quick checklist (Option C — private repo + your server)

- [ ] Build frontend: `VITE_BASE_PATH=/ npm run build` in `lab-trading-dashboard`
- [ ] Create directory on server, e.g. `/var/www/lab-dashboard`
- [ ] Upload `dist/` contents (e.g. `rsync` or deploy script)
- [ ] Nginx: serve that path for clubinfotech.com (or your chosen domain), no redirect to GitHub
- [ ] Set **API_BASE_URL** (or api-config) so the app calls **https://api.clubinfotech.com**
- [ ] Make repo **Private** on GitHub
- [ ] (Optional) Turn off GitHub Pages in repo Settings → Pages
- [ ] Test: open **https://clubinfotech.com** (or your URL) and log in

After this, the “website” is fully on your side; GitHub is only for private code and (if you want) CI.
