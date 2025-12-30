-- Initialize Jules database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

-- Create schema
CREATE SCHEMA IF NOT EXISTS jules;

-- Set search path
SET search_path TO jules, public;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA jules TO jules;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA jules TO jules;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA jules TO jules;

-- Create indexes for performance (will be created by Alembic migrations)
-- This file is mainly for initialization and can be extended as needed
