# 🐍 PyCon Community Pulse

> Real-time sentiment analysis and trend tracking for PyCon community discussions

An AI-powered microservices application that monitors and analyzes social media discussions about PyCon conferences. Built with Python, deployed on Choreo.

## 🎯 Demo Purpose

This application demonstrates:
- **Python AI Capabilities**: OpenAI integration, NLP, sentiment analysis, topic extraction
- **Choreo Platform**: Microservices deployment, API gateway, observability, auto-scaling
- **Modern Architecture**: 4 independent microservices, PostgreSQL database, REST APIs
- **Production Patterns**: Docker containers, CI/CD, configuration management

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│            Choreo API Gateway                    │
└─────────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┬──────────────┐
    ▼               ▼               ▼              ▼
┌─────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐
│   API   │  │ AI Analysis │  │Dashboard │  │Collector │
│ Service │  │   Service   │  │ Service  │  │ Service  │
│ :8000   │  │    :8001    │  │  :8002   │  │ (Worker) │
└─────────┘  └─────────────┘  └──────────┘  └──────────┘
     │             │               │              │
     └─────────────┴───────────────┴──────────────┘
                    │
          ┌─────────────────────┐
          │  PostgreSQL Database │
          └─────────────────────┘
```

### Services

1. **API Service** (Port 8000)
   - REST API for accessing posts, sentiment stats, and trends
   - Public endpoint
   - Endpoints: `/posts`, `/sentiment/stats`, `/trending/topics`

2. **AI Analysis Service** (Port 8001)
   - Sentiment analysis using OpenAI GPT-3.5
   - Topic and entity extraction
   - Internal service

3. **Dashboard Service** (Port 8002)
   - Web UI for visualizing trends
   - Real-time sentiment charts
   - Public endpoint

4. **Collector Service** (Background Worker)
   - Collects posts from Dev.to, Medium, YouTube, GitHub
   - Runs every 30 minutes
   - Stores data in PostgreSQL

## 📊 Data Sources

- **Dev.to**: Public API, no auth required
- **Medium**: RSS feeds
- **YouTube**: Video metadata (API key optional)
- **GitHub**: Repository search (token optional)

All data collected is publicly available.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- OpenAI API key
- Choreo CLI (for deployment)

### Local Development

1. **Clone and setup**
   ```bash
   cd pycon-community-pulse
   ```

2. **Setup database**
   ```bash
   createdb pycon_pulse
   psql pycon_pulse < database/schema.sql
   ```

3. **Configure environment**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost:5432/pycon_pulse"
   export OPENAI_API_KEY="your-key-here"
   ```

4. **Run services**
   ```bash
   # Terminal 1: API Service
   cd api-service && pip install -r requirements.txt && python main.py

   # Terminal 2: AI Analysis Service
   cd ai-analysis-service && pip install -r requirements.txt && python main.py

   # Terminal 3: Dashboard
   cd dashboard-service && pip install -r requirements.txt && python main.py

   # Terminal 4: Collector
   cd collector-service && pip install -r requirements.txt && python main.py
   ```

5. **Access**
   - API: http://localhost:8000
   - Dashboard: http://localhost:8002
   - API Docs: http://localhost:8000/docs

### Deploy to Choreo

1. **Login to Choreo**
   ```bash
   choreo login --org manjulacse
   ```

2. **Create project**
   ```bash
   choreo create project --name "PyCon Community Pulse"
   ```

3. **Deploy each service**
   ```bash
   # From project root
   choreo create component api-service --type service --dir api-service
   choreo create component ai-analysis-service --type service --dir ai-analysis-service
   choreo create component dashboard-service --type webApp --dir dashboard-service
   choreo create component collector-service --type scheduleTask --dir collector-service
   ```

4. **Configure secrets in Choreo console**
   - `DATABASE_URL`
   - `OPENAI_API_KEY`

5. **Build and deploy**
   ```bash
   choreo create build api-service
   choreo create deployment api-service -e=Development
   ```

## 📦 Technology Stack

### Backend
- **FastAPI**: Modern async web framework
- **SQLAlchemy**: ORM and database toolkit
- **PostgreSQL**: Primary database
- **OpenAI API**: AI-powered sentiment analysis

### Frontend
- **Jinja2**: Template engine
- **HTML/CSS**: Dashboard UI

### DevOps
- **Docker**: Containerization
- **Choreo**: Deployment platform
- **GitHub**: Version control

### Python Libraries
- `fastapi`, `uvicorn`: Web framework
- `sqlalchemy`, `psycopg2`: Database
- `openai`: AI integration
- `requests`, `feedparser`: Data collection
- `pydantic`: Data validation

## 🎓 PyCon Demo Script

### Setup (Before Demo)
1. Deploy all services to Choreo 48 hours before
2. Collector runs and gathers 50-100 real posts
3. AI service analyzes all posts
4. Verify dashboard shows data

### Demo Flow (8 minutes)

**Part 1: Show Dashboard** (2 min)
- Open dashboard, show real data
- 80+ posts collected from Dev.to, Medium, GitHub
- Sentiment: 85% positive
- Trending topics: async, FastAPI, AI, testing

**Part 2: Explain Data Collection** (2 min)
- Show collector service logs in Choreo
- Demonstrate sources: Dev.to API, Medium RSS
- All public data, no scraping
- Runs every 30 minutes automatically

**Part 3: AI Analysis** (2 min)
- Show API endpoint: `/sentiment/stats`
- Explain OpenAI integration
- Topic extraction demo
- Show analysis results for specific post

**Part 4: Choreo Platform** (2 min)
- Show all 4 services in Choreo console
- API gateway configuration
- Distributed tracing for one request
- Auto-scaling demonstration
- Logs and observability

## 🔒 Privacy & Legal

- Only public data collected
- No user authentication required
- Attribution maintained (original URLs)
- Compliant with platform ToS
- No PII stored

## 📈 Metrics & Observability

Choreo provides built-in:
- Request/response metrics
- Error rates
- Latency percentiles
- Distributed tracing
- Log aggregation

## 🛠️ Development

### Project Structure
```
pycon-community-pulse/
├── api-service/              # REST API
├── ai-analysis-service/      # AI analysis
├── dashboard-service/        # Web UI
├── collector-service/        # Data collector
├── shared/                   # Shared utilities
│   ├── config.py
│   ├── database.py
│   └── models.py
├── database/
│   └── schema.sql
└── README.md
```

### Adding a New Data Source

1. Add collector method in `collector-service/main.py`
2. Follow pattern of existing collectors
3. Return list of post dictionaries
4. Add to `collect_all()` method

## 🤝 Contributing

This is a demo application for PyCon presentations.

## 📝 License

MIT License - See LICENSE file

## 🙋 Support

For questions about this demo:
- Open an issue on GitHub
- Contact the Choreo team

---

**Built with ❤️ for the Python community**
