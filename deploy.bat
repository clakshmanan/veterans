@echo off
REM Veteran Association Management System - Windows Deployment Script
REM This script automates the deployment process on Windows

echo ==========================================
echo Veteran Association Deployment Script
echo ==========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo [INFO] Please create .env file from .env.example
    exit /b 1
)

echo [OK] .env file found

REM Activate virtual environment
if exist venv (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [WARNING] Virtual environment not found. Creating one...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment created and activated
)

REM Install/Update dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt --quiet
echo [OK] Dependencies installed

REM Run migrations
echo [INFO] Running database migrations...
python manage.py migrate --noinput
echo [OK] Migrations completed

REM Collect static files
echo [INFO] Collecting static files...
python manage.py collectstatic --noinput
echo [OK] Static files collected

REM Run Django checks
echo [INFO] Running Django system checks...
python manage.py check
echo [OK] System checks passed

REM Run deployment checks
echo [INFO] Running deployment checks...
python manage.py check --deploy
echo [OK] Deployment checks passed

REM Create superuser (optional)
set /p CREATE_SUPERUSER="Do you want to create a superuser? (y/n): "
if /i "%CREATE_SUPERUSER%"=="y" (
    python manage.py createsuperuser
)

REM Seed initial data (optional)
set /p SEED_DATA="Do you want to seed initial data? (y/n): "
if /i "%SEED_DATA%"=="y" (
    echo [INFO] Seeding initial data...
    python manage.py seed_data
    echo [OK] Initial data seeded
)

echo.
echo ==========================================
echo [SUCCESS] Deployment completed successfully!
echo ==========================================
echo.
echo [INFO] Next steps:
echo 1. Configure your web server (IIS/Apache)
echo 2. Set up SSL certificate
echo 3. Configure Windows Service
echo 4. Start application: python manage.py runserver (dev) or use Gunicorn
echo.
echo [WARNING] Remember to:
echo - Set DEBUG=False in production
echo - Use a strong SECRET_KEY
echo - Configure ALLOWED_HOSTS
echo - Set up database backups
echo - Enable monitoring and logging
echo.

pause
