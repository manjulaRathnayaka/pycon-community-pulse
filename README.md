# 🐍 PyCon Community Pulse

> Real-time sentiment analysis and trend tracking for PyCon community discussions

An AI-powered microservices application that monitors and analyzes social media discussions about PyCon conferences. Built with Python and FastAPI, deployed on Choreo.

## 🎯 Purpose

This application demonstrates:
- **Modern Python Development**: FastAPI, async/await, type hints, Pydantic models
- **Microservices Architecture**: 4 independent services with clean separation of concerns
- **AI Integration**: OpenAI-powered sentiment analysis and topic extraction
- **Choreo Platform**: Cloud-native deployment, managed databases, service connections
- **Streaming SSR**: Progressive HTML rendering for optimal user experience

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Choreo Platform                     │
└─────────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┬──────────────┐
    ▼               ▼               ▼              ▼
┌─────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐
│   API   │  │ AI Analysis │  │Dashboard │  │Collector │
│ Service │  │   Service   │  │ Service  │  │  (Task)  │
└─────────┘  └─────────────┘  └──────────┘  └──────────┘
     │             │               │              │
     └─────────────┴───────────────┴──────────────┘
                    │
          ┌─────────────────────┐
          │ Choreo PostgreSQL   │
          │   (Managed DB)      │
          └─────────────────────┘
```

### Services

1. **API Service** (FastAPI)
   - REST API for accessing posts, sentiment stats, and trends
   - Project-level visibility
   - Endpoints: `/posts`, `/sentiment/stats`, `/topics/trending`

2. **AI Analysis Service** (FastAPI)
   - Sentiment analysis using OpenAI GPT-3.5
   - Topic and entity extraction
   - Background task processing
   - Project-level visibility (internal)

3. **Dashboard Service** (FastAPI + Streaming SSR)
   - Web UI with progressive HTML streaming
   - Real-time sentiment charts
   - No client-side JavaScript data fetching
   - Public-facing

4. **Collector Service** (Scheduled Task)
   - Collects posts from Dev.to, Medium, YouTube, GitHub
   - Runs on schedule (configurable via Choreo)
   - Stores data in PostgreSQL

## 📊 Data Sources

- **Dev.to**: Public API, no auth required
- **Medium**: RSS feeds
- **YouTube**: Video metadata (API key optional)
- **GitHub**: Repository search (token optional)

All data collected is publicly available. No web scraping is performed.

## 🚀 Deploy to Choreo

You can deploy this application using either the **Choreo Console (Web UI)** or the **Choreo CLI**. The CLI method is faster and more automated.

### Prerequisites

- A Choreo account ([Sign up here](https://console.choreo.dev/))
- GitHub account with this repository forked
- OpenAI API key (for sentiment analysis)
- (Optional) [Choreo CLI installed](https://wso2.com/choreo/docs/choreo-cli/install/) for CLI deployment

---

## Option A: Deploy with Choreo CLI (Recommended)

The Choreo CLI provides a faster, scriptable way to deploy all components.

### 1. Install Choreo CLI

**macOS/Linux:**
```bash
curl -L https://github.com/wso2/choreo-cli/releases/latest/download/choreo-$(uname -s)-$(uname -m) -o choreo
chmod +x choreo
sudo mv choreo /usr/local/bin/
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://github.com/wso2/choreo-cli/releases/latest/download/choreo-windows-amd64.exe" -OutFile "choreo.exe"
```

Verify installation:
```bash
choreo version
```

### 2. Login to Choreo

```bash
choreo login
```

This opens a browser for authentication. After login, select your organization.

### 3. Create Project and Database

```bash
# Create project
choreo project create --name "PyCon Community Pulse" --description "AI-powered sentiment analysis for PyCon discussions"

# Create PostgreSQL database
choreo database create \
  --name pycon-pulse-db \
  --type postgres \
  --cloud-provider aws \
  --region us-east-1 \
  --plan hobbyist

# Wait for database to become active
choreo database get pycon-pulse-db --watch

# Publish database to marketplace
choreo database publish pycon-pulse-db
```

### 4. Deploy Services

**Deploy API Service:**
```bash
choreo component create \
  --name pycon-api \
  --type service \
  --repo https://github.com/YOUR_USERNAME/pycon-community-pulse \
  --branch main \
  --path api-service \
  --buildpack python \
  --port 8080

# Add database connection
choreo connection create \
  --component pycon-api \
  --type database \
  --target pycon-pulse-db

# Build and deploy
choreo build create --component pycon-api
choreo deployment create --component pycon-api --env Development
```

**Deploy AI Analysis Service:**
```bash
choreo component create \
  --name pycon-ai-analysis \
  --type service \
  --repo https://github.com/YOUR_USERNAME/pycon-community-pulse \
  --branch main \
  --path ai-analysis-service \
  --buildpack python \
  --port 8080

# Add database connection
choreo connection create \
  --component pycon-ai-analysis \
  --type database \
  --target pycon-pulse-db

# Add OpenAI API key
choreo config create \
  --component pycon-ai-analysis \
  --name OPENAI_API_KEY \
  --value "your-openai-api-key" \
  --type secret

# Build and deploy
choreo build create --component pycon-ai-analysis
choreo deployment create --component pycon-ai-analysis --env Development
```

**Deploy Collector Service:**
```bash
choreo component create \
  --name pycon-collector \
  --type scheduleTask \
  --repo https://github.com/YOUR_USERNAME/pycon-community-pulse \
  --branch main \
  --path collector-service \
  --buildpack python

# Add database connection
choreo connection create \
  --component pycon-collector \
  --type database \
  --target pycon-pulse-db

# Build and deploy
choreo build create --component pycon-collector
choreo deployment create \
  --component pycon-collector \
  --env Development \
  --cron "*/30 * * * *"
```

**Deploy Dashboard Service:**
```bash
choreo component create \
  --name pycon-dashboard \
  --type webapp \
  --repo https://github.com/YOUR_USERNAME/pycon-community-pulse \
  --branch main \
  --path dashboard-service \
  --buildpack python \
  --port 8080

# Connect to API service
choreo connection create \
  --component pycon-dashboard \
  --type service \
  --target pycon-api

# Build and deploy
choreo build create --component pycon-dashboard
choreo deployment create --component pycon-dashboard --env Development
```

### 5. Create Service Connections

```bash
# Connect API → AI Analysis
choreo connection create \
  --component pycon-api \
  --type service \
  --target pycon-ai-analysis
```

### 6. Get Deployment URLs

```bash
# Get dashboard URL
choreo deployment get --component pycon-dashboard --env Development

# Get API URL
choreo deployment get --component pycon-api --env Development
```

---

## Option B: Deploy with Choreo Console (Web UI)

### Step 1: Create a Project

1. Log in to [Choreo Console](https://console.choreo.dev/)
2. Click **Create** → **Project**
3. Enter project name: `PyCon Community Pulse`
4. Select your preferred region (US or EU)
5. Click **Create**

### Step 2: Create and Deploy Database

1. In your project, click **Create** → **Database**
2. Configure database:
   - **Name**: `pycon-pulse-db`
   - **Database Type**: PostgreSQL
   - **Cloud Provider**: Choose your preferred provider (AWS, GCP, Azure, DigitalOcean)
   - **Region**: Same as your project region
   - **Service Plan**: `Hobbyist` (or higher for production)
3. Click **Create**
4. Wait for database to become **Active** (5-10 minutes)
5. Go to **Marketplace** → **Databases** → Find `pycon-pulse-db` → Click **Publish**

### Step 3: Deploy API Service

1. Click **Create** → **Service**
2. Configure:
   - **Name**: `pycon-api`
   - **Description**: "REST API for PyCon posts and sentiment data"
   - **GitHub Repository**: Select your forked repository
   - **Branch**: `main` (or `refactor/clean-architecture-python-best-practices`)
   - **Buildpack**: Python
   - **Python Version**: 3.11
   - **Project Path**: `api-service/`
   - **Port**: 8080
3. Click **Create**
4. Go to **Dependencies** → **Add Connection** → **Database**:
   - Select `pycon-pulse-db` from Marketplace
   - Click **Add**
5. Go to **Configurations** → **File Mounts**:
   - Click **Add File Mount**
   - **Name**: `db-ca-certificate`
   - **Mount Path**: `/tmp/ca.pem`
   - **Config Type**: Secret
   - Upload your database CA certificate (download from database settings)
6. Go to **DevOps** → **Build** → Click **Build**
7. Wait for build to complete
8. Go to **Deploy** → **Development** → Click **Deploy**
9. Once deployed, go to **Settings** → **Endpoint** → Set visibility to **Project**

### Step 4: Deploy AI Analysis Service

1. Click **Create** → **Service**
2. Configure:
   - **Name**: `pycon-ai-analysis`
   - **Description**: "AI-powered sentiment analysis service"
   - **GitHub Repository**: Select your forked repository
   - **Branch**: `main`
   - **Buildpack**: Python
   - **Python Version**: 3.11
   - **Project Path**: `ai-analysis-service/`
   - **Port**: 8080
3. Click **Create**
4. Go to **Dependencies** → **Add Connection** → **Database**:
   - Select `pycon-pulse-db` from Marketplace
5. Go to **Configurations**:
   - **File Mounts**: Add `db-ca-certificate` (same as API service)
   - **Environment Variables**:
     - `OPENAI_API_KEY` (Secret) - Your OpenAI API key
     - `LOG_LEVEL` (String) - Optional, default: `INFO`
6. Build and deploy to Development
7. Set endpoint visibility to **Project**

### Step 5: Deploy Collector Service (Scheduled Task)

1. Click **Create** → **Scheduled Task**
2. Configure:
   - **Name**: `pycon-collector`
   - **Description**: "Collects posts from Dev.to, Medium, YouTube, GitHub"
   - **GitHub Repository**: Select your forked repository
   - **Branch**: `main`
   - **Buildpack**: Python
   - **Python Version**: 3.11
   - **Project Path**: `collector-service/`
3. Click **Create**
4. Go to **Dependencies** → **Add Connection** → **Database**:
   - Select `pycon-pulse-db` from Marketplace
5. Go to **Configurations**:
   - **File Mounts**: Add `db-ca-certificate`
   - **Environment Variables** (all optional):
     - `YOUTUBE_API_KEY` (Secret) - YouTube Data API v3 key
     - `GITHUB_TOKEN` (Secret) - GitHub personal access token
     - `COLLECTION_INTERVAL_MINUTES` (String) - Default: 30
     - `MAX_POSTS_PER_SOURCE` (String) - Default: 20
     - `LOG_LEVEL` (String) - Default: INFO
6. Build the task
7. Deploy to Development
8. Configure schedule:
   - **Cron Expression**: `*/30 * * * *` (every 30 minutes)
   - **Timezone**: Your preferred timezone

### Step 6: Deploy Dashboard Service (Web App)

1. Click **Create** → **Web Application**
2. Configure:
   - **Name**: `pycon-dashboard`
   - **Description**: "Dashboard for PyCon Community Pulse"
   - **GitHub Repository**: Select your forked repository
   - **Branch**: `main`
   - **Buildpack**: Python
   - **Python Version**: 3.11
   - **Project Path**: `dashboard-service/`
   - **Port**: 8080
3. Click **Create**
4. Go to **Dependencies** → **Add Connection** → **Service**:
   - Find `pycon-api` in Marketplace
   - Click **Add**
5. Build and deploy to Development
6. Access the dashboard URL from the **Overview** page

### Step 7: Create Service Connections

#### Connect API → AI Analysis

1. Go to `pycon-api` component
2. **Dependencies** → **Add Connection** → **Service**
3. Search for `pycon-ai-analysis` in Marketplace
4. Click **Add**
5. Redeploy API service

#### Verify Connections

All services should now be connected:
- `pycon-api` → `pycon-pulse-db` (database)
- `pycon-api` → `pycon-ai-analysis` (service)
- `pycon-ai-analysis` → `pycon-pulse-db` (database)
- `pycon-collector` → `pycon-pulse-db` (database)
- `pycon-dashboard` → `pycon-api` (service)

### Step 8: Test the Application

1. **Wait for collector** to run (or manually execute from Choreo)
2. **Check API**:
   ```bash
   curl https://your-api-url/posts
   curl https://your-api-url/sentiment/stats
   ```
3. **Trigger AI Analysis**:
   ```bash
   curl -X POST https://your-api-url/analyze
   ```
4. **View Dashboard**: Open the dashboard URL in your browser

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or use Choreo database)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/pycon-community-pulse.git
   cd pycon-community-pulse
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies for each service:
   ```bash
   cd api-service && pip install -r requirements.txt && cd ..
   cd ai-analysis-service && pip install -r requirements.txt && cd ..
   cd dashboard-service && pip install -r requirements.txt && cd ..
   cd collector-service && pip install -r requirements.txt && cd ..
   ```

4. Set up environment variables (create `.env` file in each service):
   ```bash
   # Database connection
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=pycon_pulse
   DB_USER=postgres
   DB_PASSWORD=your_password

   # API keys
   OPENAI_API_KEY=your_openai_key
   YOUTUBE_API_KEY=your_youtube_key  # optional
   GITHUB_TOKEN=your_github_token    # optional
   ```

5. Initialize database:
   ```bash
   psql -U postgres -f database/schema.sql
   ```

6. Run services:
   ```bash
   # Terminal 1 - API Service
   cd api-service && uvicorn main:app --port 8000

   # Terminal 2 - AI Analysis Service
   cd ai-analysis-service && uvicorn main:app --port 8001

   # Terminal 3 - Dashboard
   cd dashboard-service && uvicorn main:app --port 8002

   # Terminal 4 - Collector (run once)
   cd collector-service && python main.py
   ```

7. Access:
   - API: http://localhost:8000
   - Dashboard: http://localhost:8002

## 📦 Technology Stack

### Backend
- **FastAPI**: Modern async web framework with automatic OpenAPI docs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Relational database
- **OpenAI API**: GPT-3.5 for sentiment analysis
- **Pydantic**: Data validation using Python type hints

### Frontend
- **Streaming SSR**: Progressive HTML rendering
- **Jinja2**: Template engine
- **Vanilla JavaScript**: Minimal client-side code

### DevOps
- **Choreo**: Cloud platform with buildpacks
- **Google Cloud Buildpacks**: Auto-detect and build Python apps
- **GitHub**: Version control and CI/CD

### Python Libraries
- `fastapi`, `uvicorn` - Web framework and ASGI server
- `sqlalchemy`, `psycopg2-binary` - Database ORM and PostgreSQL driver
- `openai` - OpenAI API client
- `httpx` - Async HTTP client
- `requests`, `feedparser` - Data collection
- `pydantic` - Data validation

## 🎓 Demo Features

### Sentiment Analysis
- Analyzes post sentiment using OpenAI GPT-3.5
- Classifies as positive, neutral, or negative
- Confidence scores and sentiment distribution

### Topic Extraction
- Identifies trending topics from posts
- Keyword-based and AI-enhanced extraction
- Topics: async, FastAPI, AI, testing, data science, etc.

### Data Collection
- Automated collection every 30 minutes
- Sources: Dev.to, Medium, YouTube, GitHub
- Keyword-based filtering for PyCon content

### Dashboard
- Real-time sentiment charts
- Trending topics visualization
- Recent posts with sentiment badges
- Progressive loading for fast UX

## 🔒 Privacy & Legal

- **Public Data Only**: All collected data is publicly available
- **No Authentication**: No user login or personal data collected
- **Attribution**: Original post URLs and authors preserved
- **Compliant**: Follows platform Terms of Service
- **No PII**: Zero personally identifiable information stored
- **Demo Disclaimer**: Clearly marked as demonstration app

## 📈 Observability

Choreo provides built-in monitoring:
- Request/response metrics
- Error rates and logs
- Latency percentiles (P50, P95, P99)
- Distributed tracing across services
- Log aggregation and search

## 🏗️ Project Structure

```
pycon-community-pulse/
├── api-service/
│   ├── db/                    # Database models and config
│   ├── .choreo/
│   │   └── component.yaml     # Choreo configuration
│   ├── main.py                # FastAPI app
│   ├── Procfile               # Process definition
│   └── requirements.txt
├── ai-analysis-service/
│   ├── db/
│   ├── .choreo/
│   │   └── component.yaml
│   ├── main.py                # AI analysis logic
│   ├── Procfile
│   └── requirements.txt
├── dashboard-service/
│   ├── templates/
│   │   └── dashboard.html     # Streaming SSR template
│   ├── .choreo/
│   │   └── component.yaml
│   ├── main.py                # Dashboard with streaming
│   ├── Procfile
│   └── requirements.txt
├── collector-service/
│   ├── db/
│   ├── collectors.py          # Data collection logic
│   ├── .choreo/
│   │   └── component.yaml
│   ├── main.py                # Collector orchestration
│   └── requirements.txt
├── database/
│   └── schema.sql             # Database schema
└── README.md
```

## 🤝 Contributing

This is a demonstration application. Feel free to fork and adapt for your own demos!

## 📝 License

Apache License 2.0 - See [LICENSE](LICENSE) file for details

## 🙋 Support

For questions:
- Open an issue on GitHub
- Check [Choreo Documentation](https://wso2.com/choreo/docs/)

---

**Built with ❤️ for the Python community**
