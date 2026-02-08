#!/usr/bin/env bash
# Run this script ON the DB server (150.241.245.36) so the cloud (150.241.244.130) can connect to Postgres.
# Usage: copy this script to 150.241.245.36 and run as root: sudo bash open-db-port-for-cloud.sh

set -e
CLOUD_IP="150.241.244.130"

echo "→ Allowing Postgres connections from cloud $CLOUD_IP..."

# 1) PostgreSQL: listen on all interfaces (if not already)
PG_CONF=$(find /etc/postgresql -name postgresql.conf 2>/dev/null | head -1)
if [ -n "$PG_CONF" ]; then
  if ! grep -q "^listen_addresses = '\*'" "$PG_CONF" && ! grep -q "^listen_addresses = '\*'" "$PG_CONF"; then
    echo "listen_addresses = '*'" | sudo tee -a "$PG_CONF"
    echo "  Set listen_addresses in $PG_CONF"
  fi
else
  echo "  (postgresql.conf not found in /etc/postgresql; ensure Postgres listens on * or 0.0.0.0)"
fi

# 2) pg_hba.conf: allow the cloud IP
HBA=$(find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -1)
if [ -n "$HBA" ]; then
  if ! grep -q "$CLOUD_IP" "$HBA"; then
    echo "host  labdb2  postgres  ${CLOUD_IP}/32  scram-sha-256" | sudo tee -a "$HBA"
    echo "  Added $CLOUD_IP to $HBA"
  fi
  sudo systemctl reload postgresql 2>/dev/null || sudo service postgresql reload 2>/dev/null || true
else
  echo "  (pg_hba.conf not found; add line: host labdb2 postgres ${CLOUD_IP}/32 scram-sha-256)"
fi

# 3) Firewall: allow 5432 from cloud (Ubuntu ufw / or iptables)
if command -v ufw &>/dev/null; then
  sudo ufw allow from "$CLOUD_IP" to any port 5432
  sudo ufw status | head -5
elif command -v iptables &>/dev/null; then
  sudo iptables -A INPUT -p tcp -s "$CLOUD_IP" --dport 5432 -j ACCEPT
  echo "  Added iptables rule for $CLOUD_IP:5432"
fi

echo "→ Done. From the cloud, test: nc -zv $CLOUD_IP 5432 (from cloud: nc -zv 150.241.245.36 5432)"
