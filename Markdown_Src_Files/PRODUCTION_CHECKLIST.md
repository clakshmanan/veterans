# Production Deployment Checklist

## ✅ Issues Fixed

### 1. EventCategory Import Error - FIXED ✓
**Issue:** `NameError: name 'EventCategory' is not defined` at `/events/`
**Solution:** Added missing imports to views.py:
- Event
- EventCategory  
- EventRegistration
- PaymentGateway
- PaymentOrder
- PaymentWebhook

**Status:** ✅ RESOLVED

---

## 🚀 Pre-Production Checklist

### 1. Environment Configuration

- [ ] Create `.env` file from `.env.example`
- [ ] Set `DEBUG=False` in production
- [ ] Generate new `SECRET_KEY` (use: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`)
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up proper `DATABASE_URL` (PostgreSQL recommended)

### 2. Database Setup

- [ ] Migrate from SQLite to PostgreSQL for production
- [ ] Run all migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Seed initial data: `python manage.py seed_data`
- [ ] Set up database backups (daily recommended)

### 3. Static & Media Files

- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Configure media file storage (AWS S3 or similar)
- [ ] Set up CDN for static files (optional but recommended)
- [ ] Ensure proper file permissions (644 for files, 755 for directories)

### 4. Security Configuration

- [ ] Enable HTTPS/SSL certificate
- [ ] Set `SECURE_SSL_REDIRECT=True`
- [ ] Configure `CSRF_TRUSTED_ORIGINS` with your domain
- [ ] Review and update security headers
- [ ] Enable rate limiting on sensitive endpoints
- [ ] Set up firewall rules
- [ ] Configure CORS if needed

### 5. Email Configuration

- [ ] Set up SMTP server for email notifications
- [ ] Configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- [ ] Test email sending functionality
- [ ] Set up email templates for notifications

### 6. Payment Gateway Setup

- [ ] Create Razorpay account (or preferred gateway)
- [ ] Get API keys (production mode)
- [ ] Configure webhook URLs
- [ ] Test payment flow in test mode first
- [ ] Switch to production mode after testing

### 7. Logging & Monitoring

- [ ] Set up centralized logging (e.g., Sentry, CloudWatch)
- [ ] Configure error tracking
- [ ] Set up application monitoring
- [ ] Configure log rotation
- [ ] Set up alerts for critical errors

### 8. Performance Optimization

- [ ] Enable database query optimization
- [ ] Set up Redis for caching (recommended)
- [ ] Configure database connection pooling
- [ ] Optimize media file delivery
- [ ] Enable gzip compression
- [ ] Set up load balancing (if needed)

### 9. Backup & Recovery

- [ ] Set up automated database backups
- [ ] Configure media files backup
- [ ] Test restore procedures
- [ ] Document recovery process
- [ ] Set up off-site backup storage

### 10. Testing

- [ ] Test all user flows (admin, state admin, veteran)
- [ ] Test payment integration
- [ ] Test file uploads
- [ ] Test email notifications
- [ ] Perform security audit
- [ ] Load testing (if expecting high traffic)

### 11. Documentation

- [ ] Update README with production setup
- [ ] Document API endpoints (if any)
- [ ] Create user manual
- [ ] Document admin procedures
- [ ] Create troubleshooting guide

### 12. Deployment

- [ ] Choose hosting platform (AWS, DigitalOcean, Heroku, etc.)
- [ ] Set up web server (Nginx/Apache)
- [ ] Configure WSGI server (Gunicorn recommended)
- [ ] Set up process manager (Supervisor/systemd)
- [ ] Configure domain and DNS
- [ ] Set up SSL certificate (Let's Encrypt)

---

## 📋 Required Dependencies for Production

Add to `requirements.txt`:

```
Django==5.2.6
python-decouple==3.8
dj-database-url==2.1.0
psycopg2-binary==2.9.9
gunicorn==21.2.0
whitenoise==6.6.0
django-extensions==3.2.3
Pillow==10.2.0
razorpay==1.4.1
boto3==1.34.34
django-storages==1.14.2
sentry-sdk==1.40.0
redis==5.0.1
django-redis==5.4.0
```

---

## 🔧 Production Settings Updates

### settings.py additions:

```python
# Production Database
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Redis Cache (Production)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# AWS S3 Storage (Production)
if not DEBUG:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='ap-south-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    
    # Static files
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # Media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@veteranassociation.org')

# Sentry Error Tracking
if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=config('SENTRY_DSN', default=''),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False
    )
```

---

## 🚦 Deployment Commands

### Initial Deployment:

```bash
# 1. Clone repository
git clone <repository-url>
cd veteran_cg

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with production values

# 5. Run migrations
python manage.py migrate

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Create superuser
python manage.py createsuperuser

# 8. Seed initial data
python manage.py seed_data

# 9. Test the application
python manage.py check --deploy

# 10. Start with Gunicorn
gunicorn veteran_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Nginx Configuration Example:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /path/to/veteran_cg/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /path/to/veteran_cg/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service File (veteran.service):

```ini
[Unit]
Description=Veteran Association Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/veteran_cg
Environment="PATH=/path/to/veteran_cg/venv/bin"
ExecStart=/path/to/veteran_cg/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/path/to/veteran_cg/veteran.sock \
          veteran_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

---

## 🔍 Post-Deployment Verification

- [ ] Access the site via HTTPS
- [ ] Test login functionality
- [ ] Test member creation
- [ ] Test file uploads
- [ ] Test payment flow
- [ ] Verify email notifications
- [ ] Check error logging
- [ ] Monitor performance
- [ ] Review security headers
- [ ] Test backup restoration

---

## 📞 Support & Maintenance

### Regular Maintenance Tasks:

1. **Daily:**
   - Monitor error logs
   - Check application performance
   - Verify backup completion

2. **Weekly:**
   - Review security logs
   - Update dependencies (if needed)
   - Database optimization

3. **Monthly:**
   - Security audit
   - Performance review
   - Backup restoration test

### Emergency Contacts:

- System Administrator: [Contact Info]
- Database Administrator: [Contact Info]
- Security Team: [Contact Info]

---

## ✅ Status: PRODUCTION READY

All critical issues have been resolved. The application is ready for production deployment after completing the checklist above.

**Last Updated:** 2024
**Version:** 1.0.0
