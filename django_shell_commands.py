"""
Simple script to create accounts user - Run this in Django shell
python manage.py shell
"""

from django.contrib.auth.models import User
from django.db import connection

# Step 1: Create the table
with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veteran_app_accountsuser (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            approved BOOLEAN NOT NULL DEFAULT FALSE,
            full_name VARCHAR(200) NOT NULL DEFAULT '',
            designation VARCHAR(100) NOT NULL DEFAULT 'Accounts Manager',
            contact_number VARCHAR(15) NOT NULL DEFAULT '',
            email VARCHAR(254) NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES auth_user (id)
        );
    """)

# Step 2: Create user
user = User.objects.create_user(
    username='accounts',
    password='accounts123',
    email='accounts@icgvwa.org',
    first_name='Accounts',
    last_name='Manager'
)

# Step 3: Create profile
with connection.cursor() as cursor:
    cursor.execute("""
        INSERT INTO veteran_app_accountsuser 
        (user_id, approved, full_name, designation, email, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
    """, [user.id, True, 'Accounts Manager', 'Treasurer', 'accounts@icgvwa.org'])

print("✅ Accounts user created successfully!")
print("Username: accounts")
print("Password: accounts123")