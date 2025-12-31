# Security Implementation Guide - Immediate Actions

## ✅ COMPLETED FIXES

### 1. Session Security - IP Check Fixed
- **File:** `veteran_app/middleware.py`
- **Fix:** Added `ip_verified` flag to prevent logout during login
- **Status:** ✅ FIXED

### 2. Password Policy Strengthened
- **File:** `veteran_app/forms.py`
- **Changes:** Password now requires:
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
  - At least 1 special character (!@#$%^&*...)
- **Status:** ✅ FIXED

### 3. File Upload Validators Created
- **File:** `veteran_app/validators.py` (NEW)
- **Validators Added:**
  - `validate_file_extension()` - PDF, DOC, DOCX, JPG, PNG only
  - `validate_image_extension()` - JPG, PNG only
  - `validate_file_size()` - Max 5MB
  - `validate_resume_extension()` - PDF, DOC, DOCX only
  - `validate_no_html()` - Prevent HTML injection
  - `validate_no_xss()` - Prevent XSS attacks
  - `validate_no_sql_injection()` - Basic SQL injection prevention
- **Status:** ✅ CREATED (Needs to be applied to models)

### 4. Environment Variables Setup
- **Files Created:**
  - `.env` - Development configuration
  - `.env.example` - Template for production
- **Status:** ✅ CREATED

### 5. Settings.py Security Update
- **File:** `veteran_project/settings.py`
- **Changes:**
  - SECRET_KEY now required from .env (no default)
  - Database password required from .env (no default)
  - Removed hardcoded credentials
- **Status:** ✅ FIXED

---

## 🚨 IMMEDIATE ACTIONS REQUIRED

### Step 1: Apply File Upload Validators to Models

**File to Edit:** `veteran_app/models.py`

Add import at the top:
```python
from .validators import (
    validate_image_extension,
    validate_file_extension,
    validate_file_size,
    validate_resume_extension
)
```

Update these fields in **VeteranMember** model:
```python
profile_photo = models.ImageField(
    upload_to='veterans/%Y/',
    blank=True,
    null=True,
    validators=[validate_image_extension, validate_file_size]
)

document = models.FileField(
    upload_to='documents/%Y/',
    blank=True,
    null=True,
    validators=[validate_file_extension, validate_file_size]
)
```

Update **JobPortal** model:
```python
resume = models.FileField(
    upload_to='resumes/%Y/',
    blank=True,
    null=True,
    validators=[validate_resume_extension, validate_file_size]
)
```

Update **Matrimonial** model:
```python
photo = models.ImageField(
    upload_to='matrimonial/%Y/',
    blank=True,
    null=True,
    validators=[validate_image_extension, validate_file_size]
)
```

Update **Child** model:
```python
child_photo = models.ImageField(
    upload_to='children/%Y/',
    blank=True,
    null=True,
    validators=[validate_image_extension, validate_file_size]
)
```

Update **CarouselSlide** model:
```python
image = models.ImageField(
    upload_to='carousel/%Y/',
    blank=True,
    null=True,
    validators=[validate_image_extension, validate_file_size]
)
```

Update **UserState** model:
```python
profile_photo = models.ImageField(
    upload_to='state_heads/%Y/',
    blank=True,
    null=True,
    validators=[validate_image_extension, validate_file_size]
)
```

### Step 2: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 3: Change All Default Passwords

**State User Passwords:**
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
from veteran_app.models import State

# Change all state user passwords
for state in State.objects.all():
    username = f"state_{state.code}"
    try:
        user = User.objects.get(username=username)
        # Set strong password (change these!)
        user.set_password(f"Secure{state.code}@2024!")
        user.save()
        print(f"Updated password for {username}")
    except User.DoesNotExist:
        print(f"User {username} not found")
```

**Demo User Passwords:**
```python
# Change demo user password
demo_user = User.objects.get(username='demo')
demo_user.set_password('SecureDemo@2024!')
demo_user.save()
```

### Step 4: Update .env for Production

**Generate New SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Update .env file:**
```env
SECRET_KEY=<paste-generated-key-here>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_PASSWORD=<strong-database-password>
SECURE_SSL_REDIRECT=True
```

### Step 5: Add .env to .gitignore

**File:** `.gitignore`
```
.env
*.pyc
__pycache__/
db.sqlite3
media/
staticfiles/
*.log
```

---

## 🔒 AUTHORIZATION CHECKS TO ADD

### Critical Views to Audit

**File:** `veteran_app/views.py`

Add these checks to each view:

#### 1. State Detail View
```python
@login_required
def state_detail(request, state_id):
    state = get_object_or_404(State, pk=state_id)
    
    # Authorization check
    if not request.user.is_superuser:
        if not hasattr(request.user, 'state_profile') or request.user.state_profile.state != state:
            messages.error(request, "You don't have permission to access this state.")
            return redirect('index')
    
    # ... rest of view
```

#### 2. Edit Member View
```python
@login_required
def edit_member(request, member_id):
    member = get_object_or_404(VeteranMember, pk=member_id)
    
    # Authorization check
    if not request.user.is_superuser:
        if not hasattr(request.user, 'state_profile') or request.user.state_profile.state != member.state:
            messages.error(request, "You don't have permission to edit this member.")
            return redirect('index')
    
    # ... rest of view
```

#### 3. Veteran Edit Payment View
```python
@login_required
def veteran_edit_payment(request, payment_id):
    payment = get_object_or_404(Transaction, pk=payment_id)
    
    # Authorization check - users can only edit their own payments
    if not request.user.is_superuser:
        if not hasattr(request.user, 'veteran_profile') or payment.veteran != request.user.veteran_profile:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    # ... rest of view
```

---

## 🛡️ XSS PROTECTION

### Template Security Audit

**Check these templates for unsafe content:**

1. **veteran_app/templates/veteran_app/base.html**
   - Announcement text display
   - User-generated content

2. **veteran_app/templates/veteran_app/index.html**
   - Message display
   - Notification content

3. **veteran_app/templates/veteran_app/state_dashboard.html**
   - Member names and addresses
   - Announcement content

**Rule:** Never use `|safe` filter on user input. If you must display HTML, use `bleach` library:

```python
# Install: pip install bleach
import bleach

def clean_html(text):
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    return bleach.clean(text, tags=allowed_tags, strip=True)
```

---

## 📊 AUDIT LOGGING

### Add Audit Trail

**Create new model in models.py:**
```python
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('DISAPPROVE', 'Disapprove'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Change'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"
```

**Add logging to critical operations:**
```python
from .models import AuditLog

def log_action(user, action, model_name, object_id, description, request):
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        description=description,
        ip_address=get_client_ip(request)
    )

# Example usage in approve_member view:
log_action(
    user=request.user,
    action='APPROVE',
    model_name='VeteranMember',
    object_id=member.id,
    description=f"Approved member: {member.name}",
    request=request
)
```

---

## 🚀 RATE LIMITING

### Install Django Ratelimit
```bash
pip install django-ratelimit
```

### Apply to Login View
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # Check if rate limited
    if getattr(request, 'limited', False):
        messages.error(request, 'Too many login attempts. Please try again later.')
        return render(request, 'veteran_app/login.html')
    
    # ... rest of login logic
```

---

## ✅ FINAL SECURITY CHECKLIST

Before deploying to production:

- [ ] Applied file upload validators to all models
- [ ] Changed all default/seed passwords
- [ ] Generated new SECRET_KEY
- [ ] Moved all credentials to .env
- [ ] Added .env to .gitignore
- [ ] Set DEBUG=False
- [ ] Added authorization checks to all views
- [ ] Audited templates for XSS vulnerabilities
- [ ] Implemented audit logging
- [ ] Added rate limiting to login
- [ ] Enabled HTTPS (SSL/TLS)
- [ ] Configured proper ALLOWED_HOSTS
- [ ] Set up database backups
- [ ] Reviewed security.log for sensitive data
- [ ] Tested all security features
- [ ] Conducted penetration testing

---

**Status:** Security fixes implemented. Follow this guide to complete the security hardening.
**Priority:** Complete Steps 1-5 immediately before any production deployment.
