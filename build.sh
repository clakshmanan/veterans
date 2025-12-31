#!/bin/bash

# Build script for Render deployment
echo "Starting build process..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Seed initial data (master data)
echo "Seeding master data..."
python manage.py seed_data

# Seed state users (optional - comment out if not needed)
echo "Creating state users..."
python manage.py seed_state_users

# Seed sample members (optional - comment out if not needed in production)
echo "Creating sample members..."
python manage.py create_accounts_user

echo "Setting up state admin permissions..."
python manage.py state_admin_permissions

echo "Fixing state head permissions..."
python manage.py fix_state_permissions

echo "Build completed successfully!"