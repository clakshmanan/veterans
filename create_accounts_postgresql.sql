-- PostgreSQL version - Create AccountsUser table
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

-- Create accounts user with proper password hash
INSERT INTO auth_user (username, password, email, first_name, last_name, is_staff, is_active, is_superuser, date_joined)
VALUES (
    'accounts', 
    'pbkdf2_sha256$600000$salt$hash', 
    'accounts@icgvwa.org', 
    'Accounts', 
    'Manager', 
    FALSE, 
    TRUE, 
    FALSE, 
    NOW()
);

-- Create AccountsUser profile
INSERT INTO veteran_app_accountsuser (user_id, approved, full_name, designation, email, created_at, updated_at)
SELECT id, TRUE, 'Accounts Manager', 'Treasurer', 'accounts@icgvwa.org', NOW(), NOW()
FROM auth_user WHERE username = 'accounts';