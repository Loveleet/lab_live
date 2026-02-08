# Restart check (lab_live)

After a cloud or tunnel restart:

1. **Tunnel URL** – On cloud: `tail -20 /var/log/cloudflared-tunnel.log` (or the log path your tunnel uses). Copy the `https://xxx.trycloudflare.com` URL.
2. **GitHub secret** – [Settings → Secrets and variables → Actions](https://github.com/Loveleet/lab_live/settings/secrets/actions): set **API_BASE_URL** to that URL (no trailing slash).
3. **Redeploy** – [Actions](https://github.com/Loveleet/lab_live/actions) → **Deploy frontend to GitHub Pages** → Run workflow.
4. **Verify** – Open [https://loveleet.github.io/lab_live/](https://loveleet.github.io/lab_live/) and hard-refresh (Ctrl+Shift+R / Cmd+Shift+R).

If you ran `fix-api-config-and-cloud.sh`, the cloud cron will update the secret periodically; you can also run **Update API config** workflow manually.
