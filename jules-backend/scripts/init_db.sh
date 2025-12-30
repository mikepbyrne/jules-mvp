#!/bin/bash
# Initialize database with migrations

set -e

echo "🔧 Initializing Jules database..."

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "✅ PostgreSQL is ready!"

# Run migrations
echo "🔄 Running Alembic migrations..."
alembic upgrade head

echo "✅ Database initialized successfully!"
