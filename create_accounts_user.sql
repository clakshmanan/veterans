-- Step 1: Create the AccountsUser table
CREATE TABLE IF NOT EXISTS veteran_app_accountsuser (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    approved BOOLEAN NOT NULL DEFAULT 0,
    full_name VARCHAR(200) NOT NULL DEFAULT '',
    designation VARCHAR(100) NOT NULL DEFAULT 'Accounts Manager',
    contact_number VARCHAR(15) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user (id)
);

-- Step 2: Create the accounts user (password hash for 'accounts123')
INSERT INTO auth_user (username, password, email, first_name, last_name, is_staff, is_active, is_superuser, date_joined)
VALUES (
    'accounts', 
    'pbkdf2_sha256$600000$salt123$hash123', 
    'accounts@icgvwa.org', 
    'Accounts', 
    'Manager', 
    0, 
    1, 
    0, 
    datetime('now')
);

-- Step 3: Create AccountsUser profile
INSERT INTO veteran_app_accountsuser (user_id, approved, full_name, designation, email, created_at, updated_at)
SELECT id, 1, 'Accounts Manager', 'Treasurer', 'accounts@icgvwa.org', datetime('now'), datetime('now')
FROM auth_user WHERE username = 'accounts';

-- Verify the creation
SELECT 'User created:' as info, username, email FROM auth_user WHERE username = 'accounts';
SELECT 'AccountsUser profile created:' as info, full_name, designation FROM veteran_app_accountsuser;