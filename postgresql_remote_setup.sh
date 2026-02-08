#!/bin/bash

# PostgreSQL Remote Connection Setup Script
# Run this on your Ubuntu server (150.241.245.36)

echo "🔧 Setting up PostgreSQL for remote connections..."

# 1. Edit postgresql.conf to listen on all addresses
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf

# 2. Add client authentication rule for your external connections
echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf

# 3. Restart PostgreSQL to apply changes
sudo systemctl restart postgresql

# 4. Check PostgreSQL status
sudo systemctl status postgresql

# 5. Test if PostgreSQL is listening on port 5432
sudo netstat -tlnp | grep 5432

echo "✅ PostgreSQL remote connection setup complete!"
echo "📋 Connection details:"
echo "   Host: 150.241.245.36"
echo "   Port: 5432"
echo "   Database: labdb2" 
echo "   User: postgres"
echo "   Password: IndiaNepal1-"
