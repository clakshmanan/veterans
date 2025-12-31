@echo off
echo Setting up Accounts User for ICGVWA System...
echo.

cd /d "%~dp0"

python setup_accounts_user.py

echo.
echo Setup completed. Press any key to exit...
pause > nul