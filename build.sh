#!/bin/bash

# Simple build script for Render
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser..."
python manage.py create_superuser

echo "Seeding initial data..."
python manage.py seed_data || echo "Warning: seed_data failed"

echo "Build completed!"