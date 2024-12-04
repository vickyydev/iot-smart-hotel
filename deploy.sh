#!/bin/bash

# Stop and remove existing containers
docker-compose down

# Build new images
docker-compose build

# Start services
docker-compose up -d

# Wait for database
sleep 10

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser if needed
docker-compose exec web python manage.py createsuperuser --noinput

# Run tests
docker-compose exec web python manage.py test

echo "Deployment complete!"