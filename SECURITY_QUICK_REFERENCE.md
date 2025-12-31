# 🔒 Security Quick Reference Card

## 🚨 CRITICAL - DO THIS NOW

### 1. Run Security Fix Script (5 minutes)
```bash
cd d:\_koding\_veteran\veteran_cg
python apply_security_fixes.py
```
**What it does:**
- Changes all default passwords
- Checks .env configuration
- Verifies .gitignore

### 2. Generate New SECRET_KEY (1 minute)
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
**Then:** Copy output to `.env` file

### 3. Update .env File (2 minutes)
```env
SECRET_KEY=<paste-new-key-here>
DB_PASSWORD=<strong-password>
DEBUG=False  # For production only
```

---

## ⚠️ HIGH PRIORITY - DO BEFORE PRODUCTION

### 4. Apply File Upload Validators (10 minutes)

**Edit:** `veteran_app/models.py`

**Add at top:**
```python
from .validators import validate_image_extension, validate_file_extension, validate_file_size
```

**Update fields (example):**
```python
profile_photo = models.ImageField(
    upload_to='veterans/%Y/',
    validators=[validate_image_extension, validate_file_size]
)
```

**Apply to:** profile_photo, document, resume, photo, child_photo, image

**Then run:**
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Add Authorization Checks (30 minutes)

**Pattern to add to views:**
```python
@login_required
def your_view(request, id):
    # Get object
    obj = get_object_or_404(Model, pk=id)
    
    # Authorization check
    if not request.user.is_superuser:
        if not hasattr(request.user, 'state_profile') or request.user.state_profile.state != obj.state:
            messages.error(request, "Unauthorized access")
            return redirect('index')
    
    # ... rest of view
```

**Apply to:** state_detail, edit_member, delete_member, veteran_edit_payment

---

## 📋 SECURITY CHECKLIST

### Before Production Deployment

- [ ] Run `python apply_security_fixes.py`
- [ ] Generate new SECRET_KEY
- [ ] Update .env with strong passwords
- [ ] Apply file upload validators
- [ ] Add authorization checks to views
- [ ] Set DEBUG=False in .env
- [ ] Update ALLOWED_HOSTS in .env
- [ ] Enable HTTPS/SSL
- [ ] Test file upload security
- [ ] Test unauthorized access attempts
- [ ] Review security.log for issues
- [ ] Backup database
- [ ] Document admin credentials securely

---

## 🔑 NEW PASSWORDS (After Running Script)

### State Users
- **Pattern:** `Secure{STATE_CODE}@2024!`
- **Examples:**
  - state_AP: `SecureAP@2024!`
  - state_TN: `SecureTN@2024!`
  - state_KL: `SecureKL@2024!`

### Demo User
- **Username:** demo
- **Password:** `SecureDemo@2024!`

**⚠️ IMPORTANT:** Users should change these on first login!

---

## 🛡️ SECURITY FEATURES STATUS

| Feature | Status | Priority |
|---------|--------|----------|
| SQL Injection Protection | ✅ Active | - |
| CSRF Protection | ✅ Active | - |
| Session Security | ✅ Fixed | - |
| Password Policy | ✅ Strong | - |
| File Upload Validation | ⚠️ Created | HIGH |
| Authorization Checks | ⚠️ Partial | HIGH |
| XSS Protection | ⚠️ Needs Audit | MEDIUM |
| Secrets Management | ⚠️ Needs .env | CRITICAL |
| Rate Limiting | ❌ Missing | MEDIUM |
| 2FA | ❌ Missing | LOW |

---

## 📁 SECURITY DOCUMENTATION

1. **SECURITY_STATUS.md** - Current security status
2. **SECURITY_FIXES.md** - Detailed audit report
3. **SECURITY_IMPLEMENTATION_GUIDE.md** - Step-by-step guide
4. **SECURITY_QUICK_REFERENCE.md** - This file

---

## 🚀 QUICK COMMANDS

### Change User Password
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.get(username='username')
user.set_password('NewPassword@123!')
user.save()
```

### Check Security Settings
```bash
python manage.py check --deploy
```

### View Security Log
```bash
type security.log  # Windows
cat security.log   # Linux/Mac
```

### Test File Upload
```python
# Try uploading: .exe, .php, .sh files (should be blocked)
# Try uploading: >5MB files (should be blocked)
# Try uploading: .jpg, .pdf files (should work)
```

---

## ⚠️ COMMON SECURITY MISTAKES TO AVOID

1. ❌ Don't commit .env file to Git
2. ❌ Don't use DEBUG=True in production
3. ❌ Don't use default SECRET_KEY
4. ❌ Don't skip authorization checks
5. ❌ Don't trust client-side validation only
6. ❌ Don't log sensitive data (passwords, tokens)
7. ❌ Don't use predictable passwords
8. ❌ Don't expose database credentials

---

## 📞 EMERGENCY CONTACTS

### If Security Breach Detected:
1. Take site offline immediately
2. Change all passwords
3. Review security.log
4. Check database for unauthorized changes
5. Restore from backup if needed
6. Investigate breach source
7. Apply additional security measures

---

## 🎯 PRODUCTION DEPLOYMENT COMMAND

```bash
# 1. Set environment
set DJANGO_SETTINGS_MODULE=veteran_project.settings

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Run migrations
python manage.py migrate

# 4. Check deployment
python manage.py check --deploy

# 5. Start with Gunicorn (production server)
gunicorn veteran_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

---

**Remember:** Security is an ongoing process, not a one-time task!

**Last Updated:** 2024  
**Version:** 1.0
