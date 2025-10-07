"""
Dashboard Service - Web UI for PyCon Community Pulse.

Displays sentiment trends, popular topics, and recent posts in a
user-friendly web interface.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PyCon Community Pulse - Dashboard",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Get API connection details from Choreo auto-injected environment variables
# Connection name: dashboard-to-api -> env: CHOREO_DASHBOARD_TO_API_SERVICEURL
API_SERVICE_URL = os.getenv("CHOREO_DASHBOARD_TO_API_SERVICEURL", "http://localhost:8080")
API_BASE_URL = API_SERVICE_URL.rstrip('/')

# Log configuration on startup
logger.info("=" * 80)
logger.info("DASHBOARD SERVICE CONFIGURATION")
logger.info("=" * 80)
logger.info(f"API_SERVICE_URL: {API_SERVICE_URL}")
logger.info(f"API_BASE_URL: {API_BASE_URL}")
logger.info(f"PORT: {os.getenv('PORT', '8080')}")
logger.info(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'info')}")
logger.info("=" * 80)
sys.stdout.flush()
sys.stderr.flush()


# Response models
class SentimentStats(BaseModel):
    """Model for sentiment statistics."""
    positive: int = 0
    negative: int = 0
    neutral: int = 0


class PostDisplay(BaseModel):
    """Model for post display data."""
    title: str
    source: str
    url: str
    sentiment: str
    published_at: Optional[datetime]


class TopicItem(BaseModel):
    """Model for topic display."""
    topic: str
    count: int


async def call_api(endpoint: str, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """
    Call the API service with error handling.

    Args:
        endpoint: API endpoint path (e.g., "/posts")
        timeout: Request timeout in seconds

    Returns:
        JSON response as dictionary, or None if request fails
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            full_url = f"{API_BASE_URL}{endpoint}"
            logger.info(f"Calling API: {full_url}")
            response = await client.get(full_url)
            logger.info(f"API response status: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error(f"API request timeout: {API_BASE_URL}{endpoint}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error {e.response.status_code}: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"API error calling {endpoint}: {e}", exc_info=True)
            return None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """
    Render the main dashboard page.

    Fetches data from the API service and renders the dashboard template
    with sentiment statistics, trending topics, and recent posts.

    Args:
        request: FastAPI request object

    Returns:
        HTMLResponse: Rendered dashboard page
    """
    # Fetch data from API endpoints
    sentiment_data = await call_api("/sentiment/stats")
    topics_data = await call_api("/topics/trending?limit=10")
    posts_data = await call_api("/posts?limit=10")

    # Extract sentiment statistics with safe defaults
    total_posts = sentiment_data.get("total_posts", 0) if sentiment_data else 0
    analyzed_posts = sentiment_data.get("analyzed_posts", 0) if sentiment_data else 0

    sentiment_stats = SentimentStats(
        positive=sentiment_data.get("positive", 0) if sentiment_data else 0,
        negative=sentiment_data.get("negative", 0) if sentiment_data else 0,
        neutral=sentiment_data.get("neutral", 0) if sentiment_data else 0,
    )

    # Extract topics
    topics: List[TopicItem] = []
    if topics_data and "topics" in topics_data:
        topics = [
            TopicItem(topic=t["topic"], count=t["count"])
            for t in topics_data["topics"]
        ]

    # Format posts for template
    recent_posts: List[Dict[str, Any]] = []
    if posts_data and "posts" in posts_data:
        for p in posts_data["posts"]:
            published_at = None
            if p.get("published_at"):
                try:
                    published_at = datetime.fromisoformat(p["published_at"].replace('Z', '+00:00'))
                except Exception as e:
                    logger.debug(f"Error parsing date for post {p.get('id')}: {e}")

            recent_posts.append({
                "title": p.get("title") or "No title",
                "source": p.get("source", "Unknown"),
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
            "sentiment_stats": {
                "positive": sentiment_stats.positive,
                "negative": sentiment_stats.negative,
                "neutral": sentiment_stats.neutral
            },
            "topics": [{"topic": t.topic, "count": t.count} for t in topics],
            "recent_posts": recent_posts
        }
    )


@app.get("/health")
async def health() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Dict with service name and status
    """
    return {"status": "healthy", "service": "Dashboard"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    logger.info(f"Starting Dashboard service on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        reload=False  # Disable reload in production
    )
