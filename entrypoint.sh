#!/bin/bash

set -e

# Function to wait for postgres
wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    while ! nc -z db 5432; do
        sleep 1
    done
    echo "PostgreSQL started"
}

# Wait for services
wait_for_postgres

# Create required directories
mkdir -p /code/logs /code/staticfiles /code/media /code/static
chmod 777 /code/logs /code/staticfiles /code/media /code/static

# Make and apply migrations
echo "Making migrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py createsuperuser --noinput || true

# Start server
echo "Starting server..."
exec gunicorn smart_hotel_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info