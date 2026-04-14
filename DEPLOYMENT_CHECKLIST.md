# Job Brain Bot - Production Deployment Checklist

**Status:** ✅ READY FOR DEPLOYMENT  
**Version:** 0.2.0  
**Last Updated:** April 14, 2026

---

## Quick Summary

| Category | Status |
|----------|--------|
| Code Quality | ✅ All tests pass (19/19) |
| Configuration | ✅ Updated |
| Documentation | ✅ Updated |
| Database | ✅ Migrations ready |
| Security | ✅ Pass |

**Estimated Deployment Time:** 30 minutes

---

## Pre-Deployment Verification

Run these commands to verify everything works:

```powershell
# 1. Set Python path
$env:PYTHONPATH = "src"

# 2. Run all tests
python -m pytest tests/ -v

# 3. Verify all imports
python -c "from job_brain_bot.main import run; print('✓ OK')"

# 4. Verify AI modules
python -c "
from job_brain_bot.ai_intelligence import *
print('✓ AI modules OK')
"
```

Expected output:
```
============================= 19 passed in 1.XXs
✓ OK
✓ AI modules OK
```

---

## Deployment Steps (Render.com)

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Release v0.2.0: AI Intelligence Layer + Time Filtering"
git push origin main
```

### Step 2: Create Database
1. Go to [render.com](https://render.com)
2. Click "New +" → "PostgreSQL"
3. Name: `job-brain-db`
4. Plan: `Free` (or paid for production)
5. Copy the "Internal Database URL" - you'll need it in Step 3

### Step 3: Create Environment Variables
Create a `.env` file with these values (do NOT commit this):

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
DATABASE_URL=postgresql+psycopg://... (from step 2)

# AI Intelligence (optional but recommended)
AI_ANALYSIS_ENABLED=true
NETWORKING_GENERATOR_ENABLED=true
AI_PROVIDER=pattern
```

### Step 4: Deploy Worker Service
1. In Render, click "New +" → "Background Worker"
2. Name: `job-brain-bot`
3. Region: Choose closest to your users
4. Branch: `main`
5. Runtime: `Docker`
6. Plan: `Starter` ($7/month minimum for always-on)
7. Click "Create Background Worker"

### Step 5: Configure Environment Variables in Render
In your Render dashboard for the service:
1. Go to "Environment" tab
2. Add these variables:

| Key | Value | Required |
|-----|-------|----------|
| `TELEGRAM_BOT_TOKEN` | Your token from BotFather | ✅ Yes |
| `DATABASE_URL` | From PostgreSQL instance | ✅ Yes |
| `SCHEDULER_ENABLED` | `true` | ❌ No |
| `AI_ANALYSIS_ENABLED` | `true` | ❌ No |
| `NETWORKING_GENERATOR_ENABLED` | `true` | ❌ No |

### Step 6: Run Database Migrations
In Render Shell (or locally with database URL):

```bash
# Connect to database and run migrations
psql "$DATABASE_URL" -f src/job_brain_bot/migrations/001_init.sql
psql "$DATABASE_URL" -f src/job_brain_bot/migrations/002_add_posted_date.sql
```

Or use Render's SQL shell:
1. Go to your PostgreSQL instance
2. Click "SQL Shell"
3. Paste contents of both migration files and execute

### Step 7: Deploy
Click "Manual Deploy" → "Deploy latest commit"

Wait for build to complete (2-3 minutes).

---

## Post-Deployment Verification

### Test via Telegram

Send these commands to your bot:

1. **`/start`**
   - Should show welcome message with all commands including AI features

2. **`/setprofile`**
   ```
   /setprofile Software Engineer|Fresher|Bangalore|Python,JavaScript
   ```

3. **`/jobs time=24h`**
   - Should return jobs posted in last 24 hours
   - Check that `⏱ Posted: X hours ago` appears

4. **`/analyze 1`**
   - Should show AI analysis of first job
   - Check for skills, experience level, certifications

5. **`/skills 1`**
   - Should show skill gap analysis
   - Check for missing skills and learning resources

6. **`/network 1 Sarah`**
   - Should generate a cold outreach message

7. **`/referral 1 John`**
   - Should generate a referral request

8. **`/alerts on`**
   - Should enable job alerts

### Check Logs in Render
1. Go to your worker service in Render dashboard
2. Click "Logs" tab
3. Verify:
   - No startup errors
   - Bot polling started
   - Scheduler started (if enabled)
   - No repeated errors

---

## Monitoring & Maintenance

### Health Indicators
| Check | Good | Bad |
|-------|------|-----|
| Bot responds to `/start` | ✅ | ❌ |
| Logs show no errors | ✅ | ❌ |
| Jobs appear in `/jobs` | ✅ | ❌ |
| Scheduler sends alerts | ✅ | ❌ |

### Common Issues & Fixes

**Issue:** Bot doesn't respond
- **Check:** TELEGRAM_BOT_TOKEN is correct
- **Fix:** Verify token with BotFather, update in Render env vars

**Issue:** Database connection error
- **Check:** DATABASE_URL format
- **Fix:** Use `postgresql+psycopg://` (not just `postgresql://`)

**Issue:** No jobs found
- **Check:** Scraping working (look at logs)
- **Fix:** May need to wait for first scrape cycle or check internet connectivity

**Issue:** AI features disabled
- **Check:** AI_ANALYSIS_ENABLED=true in env vars
- **Fix:** Add variable and redeploy

---

## Rollback Plan

If deployment fails:

1. **Immediate:** Disable auto-deploy in Render
2. **Investigate:** Check logs for error message
3. **Fix:** Push fix to GitHub
4. **Redeploy:** Manual deploy of fixed version
5. **Nuclear option:** Reset database and start fresh (loses user data)

---

## Security Checklist

- [ ] TELEGRAM_BOT_TOKEN stored as environment variable only
- [ ] DATABASE_URL uses internal URL (not external)
- [ ] No secrets in code repository
- [ ] `.env` file in `.gitignore`
- [ ] Database has strong password (Render managed)
- [ ] Bot has privacy mode enabled (check with BotFather)

---

## Cost Estimation (Render)

| Component | Plan | Monthly Cost |
|-----------|------|--------------|
| Worker | Starter | $7 |
| PostgreSQL | Free | $0 |
| **Total** | | **$7/month** |

For production scale:
- Worker: Standard ($25/month)
- PostgreSQL: Starter ($7/month)
- **Total: ~$32/month**

---

## Files Updated in This Release

- ✅ `.env.example` - Added AI configuration
- ✅ `README.md` - Updated with AI features and commands
- ✅ `render.yaml` - Added AI environment variables
- ✅ `pyproject.toml` - Bumped version to 0.2.0

---

## Support & Documentation

- **Main Documentation:** `README.md`
- **Time Filtering:** `TIME_FILTER_IMPLEMENTATION.md`
- **AI Features:** `AI_INTELLIGENCE_IMPLEMENTATION.md`
- **Audit Report:** `DEPLOYMENT_AUDIT_REPORT.md`

---

## Success Criteria

Deployment is successful when:
- ✅ Bot responds to `/start`
- ✅ `/jobs time=24h` returns jobs with timestamps
- ✅ `/analyze` shows job requirements
- ✅ `/skills` shows gap analysis
- ✅ `/network` generates messages
- ✅ No errors in logs for 24 hours

**Ready to deploy! 🚀**
