#!/usr/bin/env python
"""
Setup script to create accounts user and run migrations
Run this script from the project directory: python setup_accounts_user.py
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veteran_project.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from veteran_app.models import AccountsUser
from django.core.management import execute_from_command_line

def main():
    print("Setting up Accounts User...")
    
    # Run migrations first
    print("1. Running migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrations completed successfully")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return
    
    # Create accounts user
    print("2. Creating accounts user...")
    username = 'accounts'
    
    try:
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"✓ User '{username}' already exists")
            user = User.objects.get(username=username)
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                password='accounts123',
                email='accounts@icgvwa.org',
                first_name='Accounts',
                last_name='Manager'
            )
            print(f"✓ User '{username}' created successfully")
        
        # Check if AccountsUser profile exists
        try:
            accounts_user = user.accounts_profile
            print(f"✓ AccountsUser profile already exists for '{username}'")
        except AccountsUser.DoesNotExist:
            # Create AccountsUser profile
            accounts_user = AccountsUser.objects.create(
                user=user,
                approved=True,
                full_name='Accounts Manager',
                designation='Treasurer',
                email='accounts@icgvwa.org'
            )
            print(f"✓ AccountsUser profile created for '{username}'")
        
        print("\n" + "="*50)
        print("ACCOUNTS USER SETUP COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Username: {username}")
        print(f"Password: accounts123")
        print(f"Role: Accounts Manager (Treasurer)")
        print(f"Access: Reports and Treasurer functionality only")
        print("\nIMPORTANT: Please change the default password after first login!")
        print("="*50)
        
    except Exception as e:
        print(f"✗ Error creating accounts user: {e}")
        return

if __name__ == '__main__':
    main()