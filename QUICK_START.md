# ⚡ Quick Start - 10 Minute Deployment

## 🎯 Super Fast Deployment Guide

### Prerequisites (2 minutes)
1. ✅ GitHub account → https://github.com/signup
2. ✅ Render account → https://render.com/register

---

## 🚀 Deploy in 5 Steps

### Step 1: Generate Secret Key (30 seconds)
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
**Copy the output** - you'll need it!

---

### Step 2: Push to GitHub (2 minutes)

```bash
# Initialize git
git init
git add .
git commit -m "Ready for deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/veteran-management.git
git branch -M main
git push -u origin main
```

---

### Step 3: Create Database on Render (2 minutes)

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"PostgreSQL"**
3. Fill in:
   - Name: `veteran-db`
   - Region: `Singapore`
   - Plan: `Free`
4. Click **"Create Database"**
5. **Copy "Internal Database URL"** (save for next step)

---

### Step 4: Create Web Service (3 minutes)

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repo
3. Fill in:
   - Name: `veteran-management`
   - Region: `Singapore`
   - Build Command: `./build.sh`
   - Start Command: `gunicorn veteran_project.wsgi:application`
   - Plan: `Free`

4. **Add Environment Variables**:
   ```
   PYTHON_VERSION = 3.11.0
   SECRET_KEY = [your generated key from Step 1]
   DEBUG = False
   ALLOWED_HOSTS = .onrender.com
   DATABASE_URL = [your database URL from Step 3]
   SECURE_SSL_REDIRECT = True
   ```

5. Click **"Create Web Service"**

---

### Step 5: Setup Admin (2 minutes)

1. Wait for deployment to complete (watch logs)
2. Click **"Shell"** tab
3. Run:
   ```bash
   python manage.py createsuperuser
   python manage.py seed_data
   ```

---

## ✅ Done!

Your app is live at: `https://veteran-management.onrender.com`

### Final Step:
Update `CSRF_TRUSTED_ORIGINS` environment variable with your actual URL:
```
CSRF_TRUSTED_ORIGINS = https://veteran-management.onrender.com
```

---

## 🎉 Success Checklist

- [x] Database created
- [x] Code deployed
- [x] Superuser created
- [x] Initial data loaded
- [x] Application accessible

---

## 📱 Access Your App

**URL**: Your Render URL (check dashboard)  
**Admin**: `/admin/`  
**Login**: Use superuser credentials

---

## 💡 Pro Tips

1. **Free tier sleeps** after 15 min → First request takes 30-60 sec
2. **Upgrade to Starter** ($7/month) for always-on
3. **Enable backups** in database settings
4. **Monitor logs** for any issues

---

## 🆘 Quick Fixes

**Build failed?**
```bash
# Check requirements.txt has all dependencies
pip freeze > requirements.txt
git commit -am "Update deps"
git push
```

**Can't connect to database?**
- Verify DATABASE_URL is correct
- Use "Internal Database URL" not "External"

**Static files missing?**
```bash
# In Render Shell
python manage.py collectstatic --no-input
```

---

**Need detailed guide?** → See `DEPLOYMENT_GUIDE.md`

**Total Time: ~10 minutes** ⏱️
