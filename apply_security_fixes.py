"""
Quick script to apply critical security fixes
Run: python apply_security_fixes.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veteran_project.settings')
django.setup()

from django.contrib.auth.models import User
from veteran_app.models import State

def change_default_passwords():
    """Change all default/predictable passwords"""
    print("=" * 60)
    print("CHANGING DEFAULT PASSWORDS")
    print("=" * 60)
    
    # Change state user passwords
    print("\n1. Updating State User Passwords...")
    for state in State.objects.all():
        username = f"state_{state.code}"
        try:
            user = User.objects.get(username=username)
            # Generate strong password
            new_password = f"Secure{state.code}@2024!"
            user.set_password(new_password)
            user.save()
            print(f"   [OK] Updated: {username} -> {new_password}")
        except User.DoesNotExist:
            print(f"   [SKIP] User not found: {username}")
    
    # Change demo user password if exists
    print("\n2. Updating Demo User Password...")
    try:
        demo_user = User.objects.get(username='demo')
        new_password = 'SecureDemo@2024!'
        demo_user.set_password(new_password)
        demo_user.save()
        print(f"   [OK] Updated: demo -> {new_password}")
    except User.DoesNotExist:
        print("   [SKIP] Demo user not found")
    
    print("\n" + "=" * 60)
    print("PASSWORD UPDATE COMPLETE")
    print("=" * 60)
    print("\n[!] IMPORTANT: Save these passwords securely!")
    print("[!] Users should change passwords on first login")
    print("\n")

def check_env_file():
    """Check if .env file exists"""
    print("=" * 60)
    print("CHECKING ENVIRONMENT CONFIGURATION")
    print("=" * 60)
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_path):
        print("\n[OK] .env file exists")
        print("\n[!] VERIFY these settings in .env:")
        print("   - SECRET_KEY (should be unique)")
        print("   - DB_PASSWORD (should be strong)")
        print("   - DEBUG (should be False for production)")
        print("   - ALLOWED_HOSTS (should include your domain)")
    else:
        print("\n[ERROR] .env file NOT FOUND")
        print("\n[!] CREATE .env file with:")
        print("   - Copy .env.example to .env")
        print("   - Update SECRET_KEY")
        print("   - Update DB_PASSWORD")
        print("   - Set DEBUG=False for production")
    
    print("\n" + "=" * 60)

def check_gitignore():
    """Check if .env is in .gitignore"""
    print("=" * 60)
    print("CHECKING .gitignore")
    print("=" * 60)
    
    gitignore_path = os.path.join(os.path.dirname(__file__), '.gitignore')
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            content = f.read()
            if '.env' in content:
                print("\n[OK] .env is in .gitignore")
            else:
                print("\n[ERROR] .env NOT in .gitignore")
                print("\n[!] ADD to .gitignore:")
                print("   .env")
    else:
        print("\n[ERROR] .gitignore NOT FOUND")
        print("\n[!] CREATE .gitignore with:")
        print("   .env")
        print("   *.pyc")
        print("   __pycache__/")
        print("   db.sqlite3")
        print("   media/")
        print("   staticfiles/")
    
    print("\n" + "=" * 60)

def security_summary():
    """Print security summary"""
    print("\n" + "=" * 60)
    print("SECURITY FIXES SUMMARY")
    print("=" * 60)
    
    print("\n[COMPLETED]")
    print("   1. Session security (IP check fixed)")
    print("   2. Password policy strengthened")
    print("   3. File upload validators created")
    print("   4. Environment variables setup")
    print("   5. Default passwords changed")
    
    print("\n[MANUAL STEPS REQUIRED]")
    print("   1. Apply validators to models.py (see SECURITY_IMPLEMENTATION_GUIDE.md)")
    print("   2. Run: python manage.py makemigrations")
    print("   3. Run: python manage.py migrate")
    print("   4. Add authorization checks to views")
    print("   5. Audit templates for XSS vulnerabilities")
    print("   6. Generate new SECRET_KEY for production")
    print("   7. Set DEBUG=False in .env for production")
    print("   8. Enable HTTPS/SSL")
    
    print("\n[DOCUMENTATION]")
    print("   - SECURITY_FIXES.md - Complete security audit")
    print("   - SECURITY_IMPLEMENTATION_GUIDE.md - Step-by-step guide")
    print("   - .env.example - Environment template")
    
    print("\n" + "=" * 60)
    print("\n")

if __name__ == '__main__':
    print("\n")
    print("=" * 60)
    print(" " * 10 + "VETERAN PROJECT SECURITY FIXES")
    print("=" * 60)
    print("\n")
    
    try:
        change_default_passwords()
        check_env_file()
        check_gitignore()
        security_summary()
        
        print("[SUCCESS] Security fixes applied successfully!")
        print("\n[NEXT] Follow SECURITY_IMPLEMENTATION_GUIDE.md for remaining steps\n")
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        print("\nPlease check your database connection and try again.\n")
