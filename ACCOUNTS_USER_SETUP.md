# Manual Setup Instructions for Accounts User

If the automated setup script doesn't work, follow these manual steps:

## Step 1: Run Migrations
Open command prompt in the project directory and run:
```
python manage.py migrate
```

## Step 2: Create Accounts User Manually

### Option A: Using Django Shell
```
python manage.py shell
```

Then run these commands in the shell:
```python
from django.contrib.auth.models import User
from veteran_app.models import AccountsUser

# Create user
user = User.objects.create_user(
    username='accounts',
    password='accounts123',
    email='accounts@icgvwa.org',
    first_name='Accounts',
    last_name='Manager'
)

# Create AccountsUser profile
accounts_user = AccountsUser.objects.create(
    user=user,
    approved=True,
    full_name='Accounts Manager',
    designation='Treasurer',
    email='accounts@icgvwa.org'
)

print("Accounts user created successfully!")
exit()
```

### Option B: Using Management Command
```
python manage.py create_accounts_user
```

## Step 3: Verify Setup
1. Start the development server: `python manage.py runserver`
2. Go to http://127.0.0.1:8000/
3. Login with:
   - Username: `accounts`
   - Password: `accounts123`
4. You should see the "Accounts" menu in the navbar with Reports and Treasurer options

## Troubleshooting

### If you get "accounts_profile" does not exist error:
1. Make sure the migration 0028_add_accounts_user.py was applied
2. Check if the AccountsUser table exists in the database
3. Verify the user has an AccountsUser profile created

### If the Accounts menu doesn't appear:
1. Make sure you're logged in as the 'accounts' user
2. Check that the AccountsUser profile has approved=True
3. Clear browser cache and refresh the page

### If login fails:
1. Verify the user was created: `python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(username='accounts').exists())"`
2. Reset password if needed: `python manage.py changepassword accounts`

## Login Credentials
- **Username:** accounts
- **Password:** accounts123 (change this after first login!)
- **Access:** Reports and Treasurer functionality only
- **Role:** Accounts Manager/Treasurer