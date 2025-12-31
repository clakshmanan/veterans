#!/bin/bash

# Veteran Association Management System - Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "=========================================="
echo "Veteran Association Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_info "Please create .env file from .env.example"
    exit 1
fi

print_success ".env file found"

# Activate virtual environment
if [ -d "venv" ]; then
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    print_success "Virtual environment created and activated"
fi

# Install/Update dependencies
print_info "Installing dependencies..."
pip install -r requirements.txt --quiet
print_success "Dependencies installed"

# Run migrations
print_info "Running database migrations..."
python manage.py migrate --noinput
print_success "Migrations completed"

# Collect static files
print_info "Collecting static files..."
python manage.py collectstatic --noinput
print_success "Static files collected"

# Run Django checks
print_info "Running Django system checks..."
python manage.py check
print_success "System checks passed"

# Run deployment checks
print_info "Running deployment checks..."
python manage.py check --deploy
print_success "Deployment checks passed"

# Create superuser (optional)
read -p "Do you want to create a superuser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

# Seed initial data (optional)
read -p "Do you want to seed initial data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Seeding initial data..."
    python manage.py seed_data
    print_success "Initial data seeded"
fi

echo ""
echo "=========================================="
print_success "Deployment completed successfully!"
echo "=========================================="
echo ""
print_info "Next steps:"
echo "1. Configure your web server (Nginx/Apache)"
echo "2. Set up SSL certificate"
echo "3. Configure systemd service"
echo "4. Start Gunicorn: gunicorn veteran_project.wsgi:application --bind 0.0.0.0:8000"
echo ""
print_warning "Remember to:"
echo "- Set DEBUG=False in production"
echo "- Use a strong SECRET_KEY"
echo "- Configure ALLOWED_HOSTS"
echo "- Set up database backups"
echo "- Enable monitoring and logging"
echo ""
