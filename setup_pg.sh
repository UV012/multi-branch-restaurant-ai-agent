#!/usr/bin/env bash
set -e

service postgresql start

# Configure postgresql to listen on all interfaces
echo "listen_addresses = '*'" >> /etc/postgresql/16/main/conf.d/listen.conf
echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/16/main/pg_hba.conf
echo "host all all ::0/0 md5" >> /etc/postgresql/16/main/pg_hba.conf

service postgresql restart

# Set postgres user password
su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'postgrespassword';\""

# Create database if not exists
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname = 'restaurant_ai'\" | grep -q 1 || psql -c \"CREATE DATABASE restaurant_ai;\""

# Enable btree_gist extension in restaurant_ai
su - postgres -c "psql -d restaurant_ai -c \"CREATE EXTENSION IF NOT EXISTS btree_gist;\""

echo "POSTGRES_SETUP_COMPLETE"
