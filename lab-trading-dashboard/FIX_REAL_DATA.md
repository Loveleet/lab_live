# Fix: Show real data on the cloud

**Credentials (same as Render / server copy.js):**
- **Cloud Ubuntu** (150.241.244.130) SSH: `DEPLOY_PASSWORD` in `.env` (e.g. 9988609709)
- **DB server** (150.241.245.36) Postgres: `DB_USER=postgres`, `DB_PASSWORD=IndiaNepal1-`, `DB_NAME=labdb2`, `DB_PORT=5432`, no SSL. The scripts set these on the cloud when pointing at the DB server.

---

## Step 1: On the DB server (150.241.245.36)

When you are logged in as root on the DB server (e.g. `root@LAB` or `root@150.241.245.36`), run these commands to allow the cloud to connect to Postgres:

```bash
cat > /tmp/open-db-port-for-cloud.sh << 'ENDOF'
#!/usr/bin/env bash
set -e
CLOUD_IP="150.241.244.130"
echo "Allowing Postgres from $CLOUD_IP..."
PG_CONF=$(find /etc/postgresql -name postgresql.conf 2>/dev/null | head -1)
[ -n "$PG_CONF" ] && (grep -q "listen_addresses" "$PG_CONF" || echo "listen_addresses = '*'" | sudo tee -a "$PG_CONF")
HBA=$(find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -1)
if [ -n "$HBA" ]; then
  grep -q "$CLOUD_IP" "$HBA" || echo "host  labdb2  postgres  ${CLOUD_IP}/32  scram-sha-256" | sudo tee -a "$HBA"
  sudo systemctl reload postgresql 2>/dev/null || sudo service postgresql reload 2>/dev/null || true
fi
command -v ufw &>/dev/null && sudo ufw allow from "$CLOUD_IP" to any port 5432
echo "Done."
ENDOF
sudo bash /tmp/open-db-port-for-cloud.sh
```

---

## Step 2: From your laptop

After Step 1 is done, run:

```bash
./scripts/fix-real-data.sh
```

or:

```bash
./scripts/point-cloud-at-db-server.sh
```

Then refresh **http://150.241.244.130:10000** to see real data.

---

## If SSH from laptop to DB server works

If you have the correct SSH password for root@150.241.245.36, put it in `.env` as `DB_SERVER_PASSWORD=...` and run:

```bash
./scripts/run-open-db-port-on-db-server.sh
./scripts/point-cloud-at-db-server.sh
```

Then refresh the dashboard.
