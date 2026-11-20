#!/bin/sh
set -e

echo "=================================================="
echo " Starting GreenGrid Containerized Service"
echo "=================================================="

# Wait for PostgreSQL to become ready
if [ -n "$POSTGRES_HOST" ]; then
  echo "==> Waiting for PostgreSQL at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
  until nc -z -v -w30 "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
    echo "Database unavailable, waiting 2 seconds..."
    sleep 2
  done
  echo "==> PostgreSQL database is ready and accepting connections!"
fi

echo "==> Running database migrations..."
python backend/manage.py migrate --noinput

echo "==> Seeding demo data (facilities, meters, tariffs, accounts)..."
python backend/manage.py seed_demo --days 30 || true

echo "==> Collecting static assets..."
python backend/manage.py collectstatic --noinput || true

echo "==> Starting web application server..."
exec "$@"

