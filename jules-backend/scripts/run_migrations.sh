#!/bin/bash
# Run database migrations

set -e

echo "Running database migrations..."

# Wait for database to be ready
until poetry run alembic current 2>/dev/null; do
    echo "Waiting for database..."
    sleep 2
done

# Run migrations
poetry run alembic upgrade head

echo "Migrations completed successfully!"
