#!/bin/bash
# ============================================
# PostgreSQL Initialization Script
# ============================================
#
# Creates the main temponest database
# Runs automatically when the container starts for the first time

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE temponest TO postgres;

    -- Log successful initialization
    SELECT 'Database temponest initialized successfully' AS status;
EOSQL
