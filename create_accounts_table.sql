-- Create AccountsUser table manually
CREATE TABLE veteran_app_accountsuser (
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

-- Create accounts user
INSERT INTO auth_user (username, password, email, first_name, last_name, is_staff, is_active, date_joined)
VALUES ('accounts', 'pbkdf2_sha256$600000$placeholder$hash', 'accounts@icgvwa.org', 'Accounts', 'Manager', 0, 1, datetime('now'));

-- Get the user ID and create AccountsUser profile
INSERT INTO veteran_app_accountsuser (user_id, approved, full_name, designation, email, created_at, updated_at)
SELECT id, 1, 'Accounts Manager', 'Treasurer', 'accounts@icgvwa.org', datetime('now'), datetime('now')
FROM auth_user WHERE username = 'accounts';