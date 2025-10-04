# PyCon Community Pulse - Deployment Guide

## 📋 **Current Status**

### ✅ **Completed**
- ✅ Application fully built (4 microservices)
- ✅ GitHub repository created and configured
- ✅ Choreo project created: "PyCon Community Pulse"
- ✅ All 4 components created in Choreo
- ✅ Component.yaml files updated to schema v1.2
- ✅ Code pushed to: https://github.com/manjulaRathnayaka/pycon-community-pulse

### 📦 **Components Created in Choreo**
1. **api-service** - REST API (Public endpoint)
2. **ai-analysis-service** - AI Analysis Engine (Project visibility)
3. **dashboard-service** - Web Dashboard (Public endpoint)
4. **collector-service** - Background Data Collector (Scheduled Task)

---

## 🚀 **Next Steps for Deployment**

### **Step 1: Set Up PostgreSQL Database**

#### **Option A: Use Choreo Managed Database (Recommended)**
1. Go to Choreo Console: https://console.eu.choreo.dev/organizations/manjulacse
2. Navigate to "PyCon Community Pulse" project
3. Look for "Data Planes" or "Databases" section
4. Create a new PostgreSQL database instance
5. Note the connection string

#### **Option B: Use External PostgreSQL (Alternative)**
Use any of these providers:
- **Neon.tech** (Free tier, serverless PostgreSQL)
  - Sign up: https://neon.tech
  - Create database: `pycon_pulse`
  - Get connection string

- **ElephantSQL** (Free tier)
  - Sign up: https://www.elephantsql.com
  - Create "Tiny Turtle" instance (free)
  - Get connection string

- **Supabase** (Free tier)
  - Sign up: https://supabase.com
  - Create project
  - Get connection string from Settings > Database

#### **Initialize Database Schema**
Once you have the database, run the schema:

```bash
# Option 1: Using psql
psql "<your-database-url>" < database/schema.sql

# Option 2: Using any PostgreSQL client
# Copy contents of database/schema.sql and execute
```

**Connection String Format:**
```
postgresql://username:password@host:5432/database_name
```

---

### **Step 2: Configure Environment Variables in Choreo**

For each component, configure the following:

#### **2.1 API Service (api-service)**
1. Go to component in Choreo Console
2. Navigate to "Configurations" or "Environment Variables"
3. Add the following:

| Variable | Value | Type | Required |
|----------|-------|------|----------|
| `DATABASE_URL` | `postgresql://user:pass@host:5432/pycon_pulse` | Secret | Yes |
| `OPENAI_API_KEY` | Your OpenAI API key | Secret | No (for basic demo) |
| `LOG_LEVEL` | `INFO` | String | No |
| `API_HOST` | `0.0.0.0` | String | No |
| `API_PORT` | `8000` | String | No |

#### **2.2 AI Analysis Service (ai-analysis-service)**
| Variable | Value | Type | Required |
|----------|-------|------|----------|
| `DATABASE_URL` | Same as above | Secret | Yes |
| `OPENAI_API_KEY` | Your OpenAI API key | Secret | Yes (for AI features) |
| `LOG_LEVEL` | `INFO` | String | No |

#### **2.3 Dashboard Service (dashboard-service)**
| Variable | Value | Type | Required |
|----------|-------|------|----------|
| `DATABASE_URL` | Same as above | Secret | Yes |
| `LOG_LEVEL` | `INFO` | String | No |

#### **2.4 Collector Service (collector-service)**
| Variable | Value | Type | Required |
|----------|-------|------|----------|
| `DATABASE_URL` | Same as above | Secret | Yes |
| `COLLECTION_INTERVAL_MINUTES` | `30` | String | No |
| `MAX_POSTS_PER_SOURCE` | `20` | String | No |
| `YOUTUBE_API_KEY` | Your YouTube API key | Secret | No |
| `GITHUB_TOKEN` | Your GitHub token | Secret | No |
| `LOG_LEVEL` | `INFO` | String | No |

---

### **Step 3: Get API Keys**

#### **OpenAI API Key** (Required for AI features)
1. Go to: https://platform.openai.com/api-keys
2. Create new API key
3. Copy and save it securely
4. Add to `OPENAI_API_KEY` in Choreo

#### **YouTube API Key** (Optional)
1. Go to: https://console.cloud.google.com/
2. Create new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API key)
5. Add to `YOUTUBE_API_KEY` in Choreo

#### **GitHub Token** (Optional)
1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `public_repo` (read access to public repos)
4. Add to `GITHUB_TOKEN` in Choreo

---

### **Step 4: Build Components**

#### **Option A: Using Choreo Console (Recommended)**
1. Go to each component in Choreo Console
2. Navigate to "Build" section
3. Click "Build" button
4. Wait for build to complete (check logs)

#### **Option B: Using Choreo CLI**
```bash
# Build all components
choreo create build api-service --project="PyCon Community Pulse" --deployment-track=main
choreo create build ai-analysis-service --project="PyCon Community Pulse" --deployment-track=main
choreo create build dashboard-service --project="PyCon Community Pulse" --deployment-track=main
choreo create build collector-service --project="PyCon Community Pulse" --deployment-track=main
```

**Note:** Builds may already be triggered automatically when components were created.

---

### **Step 5: Deploy Components**

#### **Using Choreo Console**
1. Go to each component
2. Navigate to "Deploy" section
3. Select "Development" environment
4. Click "Deploy" button
5. Wait for deployment to complete

#### **Using Choreo CLI**
```bash
# Deploy all components to Development environment
choreo create deployment api-service -e=Development --project="PyCon Community Pulse"
choreo create deployment ai-analysis-service -e=Development --project="PyCon Community Pulse"
choreo create deployment dashboard-service -e=Development --project="PyCon Community Pulse"
choreo create deployment collector-service -e=Development --project="PyCon Community Pulse"
```

---

### **Step 6: Verify Deployment**

#### **6.1 Check Component Status**
1. Go to Choreo Console
2. Navigate to "PyCon Community Pulse" project
3. Verify all components show "Running" status

#### **6.2 Test API Service**
```bash
# Get the API endpoint URL from Choreo Console, then:
curl https://<api-service-url>/

# Should return:
# {"service":"PyCon Community Pulse API","status":"healthy","version":"1.0.0"}

# Test posts endpoint
curl https://<api-service-url>/posts

# Test sentiment stats
curl https://<api-service-url>/sentiment/stats
```

#### **6.3 Test Dashboard**
1. Get dashboard URL from Choreo Console
2. Open in browser: `https://<dashboard-url>/`
3. Should see PyCon Community Pulse dashboard
4. Initially will show "No data yet" (normal)

#### **6.4 Trigger Collector**
The collector runs as a scheduled task. To manually trigger:
1. Go to collector-service in Choreo Console
2. Navigate to "Executions" or "Manual Trigger"
3. Click "Execute" to run collector immediately
4. Check logs to see data collection progress

**Or wait 30 minutes for automatic execution.**

---

### **Step 7: Monitor Data Collection**

#### **7.1 Check Collector Logs**
1. Go to collector-service in Choreo Console
2. Navigate to "Logs"
3. Look for:
   ```
   🔍 Starting data collection...
   ✅ Collected X posts from Dev.to
   ✅ Collected X posts from Medium
   💾 Saved X new posts
   ```

#### **7.2 Verify Database**
```bash
# Connect to your PostgreSQL database
psql "<your-database-url>"

# Check posts
SELECT COUNT(*) FROM posts;
SELECT source, COUNT(*) FROM posts GROUP BY source;

# Check if analysis is running
SELECT COUNT(*) FROM sentiment_analysis;
```

#### **7.3 Trigger AI Analysis**
```bash
# Call AI analysis endpoint to analyze pending posts
curl -X POST https://<ai-analysis-service-url>/analyze/pending
```

#### **7.4 View Results in Dashboard**
1. Refresh dashboard in browser
2. Should now see:
   - Total posts count
   - Sentiment distribution (positive/negative/neutral)
   - Trending topics (async, FastAPI, AI, etc.)
   - Recent posts with sentiment badges

---

## 📊 **Expected Data Flow**

1. **Collector runs** (every 30 min) → Fetches posts from Dev.to, Medium, etc.
2. **Posts saved** to database → marked as `analyzed = false`
3. **AI Analysis service** → Processes pending posts
4. **Sentiment & topics** → Saved to database
5. **Dashboard** → Displays real-time insights
6. **API** → Provides programmatic access

---

## 🔧 **Troubleshooting**

### **Issue: No data in dashboard**
**Solution:**
1. Check collector logs - is it running?
2. Manually trigger collector execution
3. Check database - `SELECT COUNT(*) FROM posts;`
4. If posts exist but no analysis, trigger AI service manually

### **Issue: Build failures**
**Solution:**
1. Check build logs in Choreo Console
2. Verify Dockerfile syntax
3. Ensure component.yaml is valid (schema v1.2)
4. Check if all dependencies are in requirements.txt

### **Issue: Database connection errors**
**Solution:**
1. Verify DATABASE_URL format is correct
2. Test connection: `psql "<DATABASE_URL>"`
3. Check if database allows connections from Choreo IPs
4. Verify database schema is initialized

### **Issue: OpenAI API errors**
**Solution:**
1. Verify OPENAI_API_KEY is valid
2. Check API quota/billing
3. App will fallback to simple sentiment analysis if OpenAI fails

---

## 🎯 **PyCon Demo Checklist**

### **Before Demo (48 hours)**
- [ ] Deploy all services to Choreo
- [ ] Configure DATABASE_URL and OPENAI_API_KEY
- [ ] Run collector manually to gather initial data
- [ ] Verify 50-100 posts are collected
- [ ] Confirm AI analysis has run on all posts
- [ ] Test dashboard shows data correctly
- [ ] Test all API endpoints

### **Demo Day Preparation**
- [ ] Verify all services are "Running"
- [ ] Check recent data collection (last 24 hours)
- [ ] Prepare to show:
  - Dashboard with live sentiment stats
  - Trending topics word cloud
  - API endpoints with real data
  - Choreo console (services, logs, metrics)
  - Architecture diagram

### **Demo Flow (8 minutes)**
1. **Show Dashboard** (2 min)
   - Live sentiment stats
   - Trending topics
   - Recent posts with sentiment

2. **Explain Architecture** (2 min)
   - 4 microservices
   - Data sources (Dev.to, Medium, etc.)
   - AI-powered analysis

3. **Show Choreo Platform** (2 min)
   - All services deployed
   - Observability (logs, metrics)
   - Auto-scaling capabilities
   - API gateway

4. **Live API Demo** (2 min)
   - Call `/sentiment/stats` endpoint
   - Show trending topics API
   - Demonstrate real-time data

---

## 📞 **Support & Resources**

### **Project Links**
- **GitHub Repo**: https://github.com/manjulaRathnayaka/pycon-community-pulse
- **Choreo Console**: https://console.eu.choreo.dev/organizations/manjulacse/projects
- **Choreo Docs**: https://wso2.com/choreo/docs/

### **Key Files**
- `database/schema.sql` - Database schema
- `.choreo/component.yaml` - Component configurations (each service)
- `README.md` - Application documentation
- `DEPLOYMENT.md` - This file

### **API Endpoints (Once Deployed)**
- **API Service**: `https://<api-url>/`
- **Dashboard**: `https://<dashboard-url>/`
- **API Docs**: `https://<api-url>/docs` (FastAPI auto-generated)

---

## 🎉 **You're Ready!**

Once all steps are complete:
- ✅ Database is running and initialized
- ✅ All 4 services are deployed
- ✅ Collector has gathered data
- ✅ AI analysis is complete
- ✅ Dashboard shows beautiful visualizations
- ✅ APIs are responding correctly

**Your PyCon demo is ready to impress! 🚀**

---

**Last Updated**: 2025-10-04
**Choreo CLI Version**: v1.2.23
**Component Schema Version**: 1.2
