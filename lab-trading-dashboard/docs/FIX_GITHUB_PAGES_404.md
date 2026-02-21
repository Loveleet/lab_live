# Why GitHub Pages 404 wasn’t “fixed in code” — and how to fix it

## Why the 404 can’t be fixed from this repo

- The **404** is returned by **your backend** at **api.clubinfotech.com** (your cloud server), not by the frontend or GitHub Pages.
- The frontend on GitHub Pages only **calls** that URL. It cannot change whether the server responds 200 or 404.
- So the fix has to happen **on the server** (Node running, nginx proxying). No frontend change can make api.clubinfotech.com return 200 if the server is down or misconfigured.

## What to run to fix it (one time, then when it breaks again)

### Option A: Deploy script (recommended)

From your laptop (from repo root or `lab-trading-dashboard`):

```bash
cd lab-trading-dashboard
python3 scripts/deploy-server-to-cloud.py
```

This will:

1. Copy `server.js` to the cloud  
2. Restart **lab-trading-dashboard** (Node)  
3. Start **api-signals**  
4. Check that `https://api.clubinfotech.com/api/health` returns 200  

If step 4 fails, the script will warn you. Then do Option B.

### Option B: Restart manually on the cloud

```bash
ssh root@150.241.244.130
sudo systemctl restart lab-trading-dashboard
sudo systemctl status lab-trading-dashboard   # must show "active (running)"
```

Then from your laptop, verify:

```bash
bash lab-trading-dashboard/scripts/verify-api-from-laptop.sh
```

You should see: `/api/health -> 200 OK`.

### After the backend is up

1. Open **https://loveleet.github.io/lab_live/** and do a **hard refresh** (Ctrl+Shift+R or Cmd+Shift+R).  
2. The 404s should stop and data should load.

## If it still returns 404

Then either:

- **Node** is not running on the cloud → check `systemctl status lab-trading-dashboard` and logs:  
  `sudo journalctl -u lab-trading-dashboard -n 50 --no-pager`
- **Nginx** is not proxying to Node → see **docs/WHAT_RUNS_WHERE_AND_404_FIX.md** (nginx config, proxy_pass to port 10000).

Summary: **the 404 is from your server; fix it by deploying/restarting the backend and checking with the verify script.**
