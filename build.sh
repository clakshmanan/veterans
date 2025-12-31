#!/bin/bash

# Build script for Render deployment
echo "Starting build process..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Verify installations
echo "Verifying installations..."
python -c "import django; print(f'Django {django.get_version()} installed')"
python -c "import gunicorn; print('Gunicorn installed')"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Seed initial data with error handling
echo "Seeding master data..."
python manage.py seed_data || echo "Warning: seed_data failed"

echo "Creating state users..."
python manage.py seed_state_users || echo "Warning: seed_state_users failed"

echo "Build completed successfully!"