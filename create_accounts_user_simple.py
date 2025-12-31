"""
Simple script to create accounts user
Run this in Django shell: python manage.py shell < create_accounts_user_simple.py
"""

from django.contrib.auth.models import User

# Create accounts user
username = 'accounts'
password = 'accounts123'

try:
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists")
    else:
        user = User.objects.create_user(
            username=username,
            password=password,
            email='accounts@icgvwa.org',
            first_name='Accounts',
            last_name='Manager'
        )
        print(f"User '{username}' created successfully")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print("You can now login with these credentials")
        
except Exception as e:
    print(f"Error: {e}")