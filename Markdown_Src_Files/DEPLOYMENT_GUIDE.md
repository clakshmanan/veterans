# 🚀 Veteran Management System - Render Deployment Guide

## 📋 Prerequisites

- GitHub account
- Render account (free tier available at https://render.com)
- Your application code ready

---

## 🎯 Step-by-Step Deployment

### Step 1: Prepare Your Code

1. **Create `.env` file locally** (for testing):
   ```bash
   cp .env.example .env
   ```

2. **Generate a new SECRET_KEY**:
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copy the output and save it for later.

3. **Test locally with PostgreSQL** (optional but recommended):
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   
   # Test server
   python manage.py runserver
   ```

---

### Step 2: Push to GitHub

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Ready for deployment"
   ```

2. **Create GitHub repository**:
   - Go to https://github.com/new
   - Name: `veteran-management-system`
   - Keep it Private (recommended)
   - Don't initialize with README

3. **Push your code**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/veteran-management-system.git
   git branch -M main
   git push -u origin main
   ```

---

### Step 3: Deploy on Render

#### A. Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

#### B. Create PostgreSQL Database

1. **From Render Dashboard**:
   - Click "New +" → "PostgreSQL"
   
2. **Configure Database**:
   - **Name**: `veteran-db`
   - **Database**: `veteran_db`
   - **User**: `veteran_user`
   - **Region**: Singapore (or closest to your users)
   - **Plan**: Free (or Starter for production)
   
3. **Create Database** → Wait for provisioning (2-3 minutes)

4. **Copy Connection Details**:
   - Click on your database
   - Copy "Internal Database URL" (starts with `postgresql://`)
   - Save this for later

#### C. Create Web Service

1. **From Render Dashboard**:
   - Click "New +" → "Web Service"
   
2. **Connect Repository**:
   - Select your GitHub repository
   - Click "Connect"

3. **Configure Web Service**:
   
   **Basic Settings:**
   - **Name**: `veteran-management`
   - **Region**: Singapore (same as database)
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn veteran_project.wsgi:application`
   - **Plan**: Free (or Starter for production)

4. **Environment Variables** (Click "Advanced" → "Add Environment Variable"):

   Add these one by one:

   ```
   PYTHON_VERSION = 3.11.0
   ```

   ```
   SECRET_KEY = [paste your generated secret key]
   ```

   ```
   DEBUG = False
   ```

   ```
   ALLOWED_HOSTS = .onrender.com
   ```

   ```
   DATABASE_URL = [paste your PostgreSQL Internal Database URL]
   ```

   ```
   SECURE_SSL_REDIRECT = True
   ```

   ```
   CSRF_TRUSTED_ORIGINS = https://veteran-management.onrender.com
   ```
   *(Replace with your actual Render URL after deployment)*

5. **Create Web Service** → Wait for deployment (5-10 minutes)

---

### Step 4: Post-Deployment Setup

1. **Access Render Shell**:
   - Go to your web service dashboard
   - Click "Shell" tab
   - Run these commands:

   ```bash
   # Create superuser
   python manage.py createsuperuser
   
   # Seed initial data
   python manage.py seed_data
   ```

2. **Update CSRF_TRUSTED_ORIGINS**:
   - Copy your Render URL (e.g., `https://veteran-management.onrender.com`)
   - Go to Environment Variables
   - Update `CSRF_TRUSTED_ORIGINS` with your actual URL
   - Save changes (will trigger redeploy)

3. **Test Your Application**:
   - Visit your Render URL
   - Login with superuser credentials
   - Test key features

---

## 🔧 Configuration Reference

### Environment Variables Explained

| Variable | Value | Description |
|----------|-------|-------------|
| `PYTHON_VERSION` | `3.11.0` | Python runtime version |
| `SECRET_KEY` | `[generated]` | Django secret key (keep secure!) |
| `DEBUG` | `False` | Production mode |
| `ALLOWED_HOSTS` | `.onrender.com` | Allowed domains |
| `DATABASE_URL` | `postgresql://...` | Database connection string |
| `SECURE_SSL_REDIRECT` | `True` | Force HTTPS |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app.onrender.com` | CSRF protection |

---

## 📊 Monitoring & Maintenance

### View Logs
1. Go to your web service dashboard
2. Click "Logs" tab
3. Monitor for errors

### Database Backups
1. Go to your database dashboard
2. Click "Backups" tab
3. Enable automatic backups (recommended)

### Update Application
```bash
# Make changes locally
git add .
git commit -m "Update description"
git push origin main

# Render will auto-deploy
```

---

## 🎨 Optional: Custom Domain

1. **In Render Dashboard**:
   - Go to your web service
   - Click "Settings" → "Custom Domain"
   - Add your domain (e.g., `veterans.yourdomain.com`)

2. **Update DNS**:
   - Add CNAME record pointing to your Render URL
   - Wait for DNS propagation (5-30 minutes)

3. **Update Environment Variables**:
   - Add your custom domain to `ALLOWED_HOSTS`
   - Add to `CSRF_TRUSTED_ORIGINS`

---

## 🐛 Troubleshooting

### Issue: Build Failed
**Solution**: Check build logs for missing dependencies
```bash
# Add missing package to requirements.txt
pip freeze > requirements.txt
git commit -am "Update requirements"
git push
```

### Issue: Database Connection Error
**Solution**: Verify DATABASE_URL is correct
- Check for typos
- Ensure using "Internal Database URL"
- Restart web service

### Issue: Static Files Not Loading
**Solution**: Run collectstatic manually
```bash
# In Render Shell
python manage.py collectstatic --no-input
```

### Issue: 502 Bad Gateway
**Solution**: Check application logs
- Look for Python errors
- Verify gunicorn is starting
- Check ALLOWED_HOSTS includes your domain

---

## 💰 Cost Estimate

### Free Tier (Development/Testing)
- Web Service: Free (sleeps after 15 min inactivity)
- PostgreSQL: Free (limited storage)
- **Total: $0/month**

### Starter Tier (Production)
- Web Service: $7/month (always on)
- PostgreSQL: $7/month (1GB storage)
- **Total: $14/month**

### Professional Tier (High Traffic)
- Web Service: $25/month
- PostgreSQL: $20/month
- **Total: $45/month**

---

## 📞 Support

### Render Support
- Documentation: https://render.com/docs
- Community: https://community.render.com
- Status: https://status.render.com

### Application Issues
- Check logs in Render dashboard
- Review Django error messages
- Test locally first

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] PostgreSQL database created on Render
- [ ] Web service created and connected to repo
- [ ] All environment variables configured
- [ ] Build completed successfully
- [ ] Superuser created
- [ ] Initial data seeded
- [ ] CSRF_TRUSTED_ORIGINS updated with actual URL
- [ ] Application tested and working
- [ ] Database backups enabled
- [ ] Monitoring set up

---

## 🎉 Success!

Your Veteran Management System is now live on Render!

**Next Steps:**
1. Share the URL with your team
2. Set up regular database backups
3. Monitor application performance
4. Plan for scaling if needed

**Your Application URL:**
`https://veteran-management.onrender.com`

---

## 📝 Notes

- Free tier services sleep after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up
- Upgrade to Starter plan for always-on service
- Database is persistent even on free tier
- SSL certificates are automatic and free

---

**Deployment Package Created By: Amazon Q**  
**Date: 2024**  
**Version: 1.0**
