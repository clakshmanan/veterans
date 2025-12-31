# 🔄 Database Migration Guide
## SQLite → PostgreSQL (Localhost → Render)

---

## 📊 Migration Strategy

### Option 1: Fresh Start (Recommended for New Deployments)
- Deploy to Render with empty database
- Manually re-enter critical data
- Best for: Testing, small datasets

### Option 2: Data Export/Import (Recommended for Production)
- Export data from SQLite
- Import to PostgreSQL on Render
- Best for: Existing data, 1 lakh+ records

---

## 🎯 Option 1: Fresh Start

### Step 1: Deploy Application
Follow `QUICK_START.md` or `DEPLOYMENT_GUIDE.md`

### Step 2: Create Superuser
```bash
# In Render Shell
python manage.py createsuperuser
```

### Step 3: Seed Master Data
```bash
python manage.py seed_data
```

### Step 4: Manually Add Critical Data
- Login to admin panel
- Add states, ranks, branches
- Add initial members

**Time Required**: 30 minutes  
**Best For**: New deployments, testing

---

## 🎯 Option 2: Full Data Migration

### Step 1: Export from SQLite (Local)

```bash
# Export all data (excluding sessions, contenttypes)
python manage.py dumpdata \
  --natural-foreign \
  --natural-primary \
  --exclude contenttypes \
  --exclude auth.Permission \
  --exclude sessions \
  --indent 2 \
  > data_backup.json
```

**This creates**: `data_backup.json` with all your data

### Step 2: Deploy to Render
Follow deployment guide to set up application on Render

### Step 3: Upload Data File

**Method A: Using Git**
```bash
# Add data file to repo (if not too large)
git add data_backup.json
git commit -m "Add data backup"
git push

# Render will redeploy with the file
```

**Method B: Using Render Shell**
```bash
# In Render Shell, create file
cat > data_backup.json << 'EOF'
[paste your JSON content here]
EOF
```

**Method C: Using SCP/SFTP** (if Render supports)
- Upload via file transfer

### Step 4: Import Data (Render Shell)

```bash
# Load data into PostgreSQL
python manage.py loaddata data_backup.json
```

**Time Required**: 1-2 hours  
**Best For**: Production migration, large datasets

---

## 🎯 Option 3: Localhost PostgreSQL → Render PostgreSQL

### Step 1: Setup Localhost PostgreSQL

1. **Install PostgreSQL locally**:
   - Windows: https://www.postgresql.org/download/windows/
   - Mac: `brew install postgresql`
   - Linux: `sudo apt install postgresql`

2. **Create local database**:
   ```bash
   createdb veteran_local
   ```

3. **Update local settings.py**:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'veteran_local',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

4. **Migrate SQLite data to local PostgreSQL**:
   ```bash
   # Export from SQLite
   python manage.py dumpdata --natural-foreign --natural-primary \
     --exclude contenttypes --exclude auth.Permission \
     --exclude sessions > data.json
   
   # Switch to PostgreSQL in settings
   # Run migrations
   python manage.py migrate
   
   # Import data
   python manage.py loaddata data.json
   ```

### Step 2: Dump PostgreSQL Database

```bash
# Create SQL dump
pg_dump -U your_username -h localhost veteran_local > veteran_backup.sql
```

### Step 3: Get Render PostgreSQL Credentials

1. Go to Render dashboard
2. Click on your PostgreSQL database
3. Copy connection details:
   - Host
   - Port
   - Database
   - Username
   - Password

### Step 4: Restore to Render PostgreSQL

```bash
# Connect and restore
psql -h [render_host] \
     -U [render_user] \
     -d [render_database] \
     -p [render_port] \
     < veteran_backup.sql
```

**Enter password when prompted**

**Time Required**: 2-3 hours  
**Best For**: Large datasets, complex migrations

---

## 📋 Pre-Migration Checklist

- [ ] Backup current SQLite database
- [ ] Test export/import locally first
- [ ] Verify all data exports correctly
- [ ] Check file size (< 100MB recommended)
- [ ] Document any custom data
- [ ] Note down superuser credentials

---

## 🔍 Verify Migration

### Check Record Counts

```bash
# In Render Shell
python manage.py shell

# Run these commands:
from veteran_app.models import *

print(f"States: {State.objects.count()}")
print(f"Ranks: {Rank.objects.count()}")
print(f"Branches: {Branch.objects.count()}")
print(f"Blood Groups: {BloodGroup.objects.count()}")
print(f"Veterans: {VeteranMember.objects.count()}")
print(f"Users: {User.objects.count()}")
```

### Test Application

1. Login with superuser
2. Check all states load
3. Verify member data
4. Test CRUD operations
5. Check file uploads work

---

## 🐛 Troubleshooting

### Issue: "Duplicate key value violates unique constraint"

**Solution**: Reset sequences
```bash
# In Render Shell
python manage.py sqlsequencereset veteran_app | python manage.py dbshell
```

### Issue: "Foreign key constraint violation"

**Solution**: Load data in correct order
```bash
# Export with natural keys
python manage.py dumpdata --natural-foreign --natural-primary > data.json
```

### Issue: "File too large to upload"

**Solution**: Split data
```bash
# Export by model
python manage.py dumpdata veteran_app.State > states.json
python manage.py dumpdata veteran_app.Rank > ranks.json
python manage.py dumpdata veteran_app.VeteranMember > members.json

# Import separately
python manage.py loaddata states.json
python manage.py loaddata ranks.json
python manage.py loaddata members.json
```

### Issue: "Media files not migrated"

**Solution**: Upload media separately
```bash
# Compress media folder
tar -czf media.tar.gz media/

# Upload to cloud storage (AWS S3, Cloudinary)
# Update MEDIA_URL and MEDIA_ROOT in settings
```

---

## 💾 Backup Strategy

### Automated Backups (Render)

1. Go to database dashboard
2. Enable automatic backups
3. Set retention period (7-30 days)

### Manual Backups

```bash
# Weekly backup
pg_dump -h [render_host] -U [render_user] -d [render_db] > backup_$(date +%Y%m%d).sql
```

---

## 📊 Performance Optimization

### After Migration

1. **Create Indexes**:
   ```bash
   python manage.py shell
   
   from django.db import connection
   cursor = connection.cursor()
   cursor.execute("CREATE INDEX idx_veteran_state ON veteran_app_veteranmember(state_id);")
   cursor.execute("CREATE INDEX idx_veteran_approved ON veteran_app_veteranmember(approved);")
   ```

2. **Analyze Tables**:
   ```sql
   ANALYZE veteran_app_veteranmember;
   ANALYZE veteran_app_state;
   ```

3. **Vacuum Database**:
   ```sql
   VACUUM ANALYZE;
   ```

---

## ✅ Post-Migration Checklist

- [ ] All data migrated successfully
- [ ] Record counts match
- [ ] Superuser can login
- [ ] All features working
- [ ] Media files accessible
- [ ] Backups enabled
- [ ] Performance optimized
- [ ] Old database backed up

---

## 🎉 Migration Complete!

Your data is now on PostgreSQL and ready for production!

**Next Steps:**
1. Monitor application for 24-48 hours
2. Keep SQLite backup for 1 week
3. Set up monitoring alerts
4. Document any issues

---

**Migration Support**: Check logs and test thoroughly before going live!
