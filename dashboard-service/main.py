"""
Dashboard Service - Web UI for PyCon Community Pulse
Displays sentiment trends, popular topics, and posts
"""
import os
from datetime import datetime
import uvicorn
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="PyCon Community Pulse - Dashboard",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Get API connection details from Choreo environment variables
API_SERVICE_URL = os.getenv("CHOREO_API_SERVICE_CONNECTION_SERVICEURL", "http://localhost:8080")
API_KEY = os.getenv("CHOREO_API_SERVICE_CONNECTION_CHOREOAPIKEY", "")

# For local development, use config.js style URL (when deployed, it will be injected)
# This allows the dashboard to work both locally and in Choreo
API_BASE_URL = API_SERVICE_URL.rstrip('/')


async def call_api(endpoint: str):
    """Helper function to call the API service"""
    headers = {}
    if API_KEY:
        headers["apikey"] = API_KEY

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{API_BASE_URL}{endpoint}", headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling API {endpoint}: {e}")
            return None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""

    # Fetch data from API endpoints
    sentiment_data = await call_api("/sentiment/stats")
    topics_data = await call_api("/topics/trending?limit=10")
    posts_data = await call_api("/posts?limit=10")

    # Extract data with safe defaults
    total_posts = sentiment_data.get("total_posts", 0) if sentiment_data else 0
    analyzed_posts = sentiment_data.get("analyzed_posts", 0) if sentiment_data else 0

    sentiment_stats = {
        "positive": sentiment_data.get("positive", 0) if sentiment_data else 0,
        "negative": sentiment_data.get("negative", 0) if sentiment_data else 0,
        "neutral": sentiment_data.get("neutral", 0) if sentiment_data else 0,
    }

    topics = topics_data.get("topics", []) if topics_data else []

    # Format posts for template
    recent_posts = []
    if posts_data and "posts" in posts_data:
        for p in posts_data["posts"]:
            published_at = None
            if p.get("published_at"):
                try:
                    published_at = datetime.fromisoformat(p["published_at"].replace('Z', '+00:00'))
                except:
                    pass

            recent_posts.append({
                "title": p.get("title") or "No title",
                "source": p.get("source", "Unknown"),
                "author": p.get("author"),
                "url": p.get("url", "#"),
                "sentiment": "unknown",  # Will be enhanced when API returns sentiment with posts
                "published_at": published_at
            })

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_posts": total_posts,
            "analyzed_posts": analyzed_posts,
            "sentiment_stats": sentiment_stats,
            "topics": topics,
            "recent_posts": recent_posts
        }
    )


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "Dashboard"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=log_level
    )
