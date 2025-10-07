"""
Dashboard Service - Web UI for PyCon Community Pulse.

Displays sentiment trends, popular topics, and recent posts in a
user-friendly web interface.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

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


async def stream_dashboard() -> AsyncGenerator[str, None]:
    """
    Generate HTML chunks progressively as data arrives.

    This async generator:
    1. Yields HTML head + page shell immediately (fast first paint)
    2. Fetches API data in parallel
    3. Streams data chunks as they arrive using inline <script> tags
    4. Closes the HTML document

    Yields:
        str: HTML chunks to be streamed to the browser
    """
    # Yield HTML head and initial shell immediately
    yield """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyCon Community Pulse</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #306998 0%, #FFD43B 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .disclaimer {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            color: #856404;
        }
        .disclaimer h3 { margin-bottom: 10px; color: #856404; }
        .disclaimer ul { margin-left: 20px; margin-top: 10px; }
        .disclaimer li { margin-bottom: 5px; }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        .header h1 { font-size: 3em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2em; opacity: 0.95; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stat-card h3 { color: #306998; font-size: 2.5em; margin-bottom: 8px; }
        .stat-card p { color: #666; font-size: 0.9em; text-transform: uppercase; }
        .sentiment {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .sentiment h2 { margin-bottom: 20px; color: #333; }
        .sentiment-bar {
            display: flex;
            height: 60px;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        .sentiment-positive { background: #10b981; }
        .sentiment-neutral { background: #f59e0b; }
        .sentiment-negative { background: #ef4444; }
        .sentiment-legend {
            display: flex;
            justify-content: space-around;
            font-size: 0.9em;
        }
        .sentiment-legend span { display: flex; align-items: center; }
        .sentiment-legend .dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .topics {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .topics h2 { margin-bottom: 20px; color: #333; }
        .topic-cloud {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }
        .topic-tag {
            background: #306998;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .posts {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .posts h2 { margin-bottom: 20px; color: #333; }
        .post-item {
            border-left: 4px solid #306998;
            padding: 16px;
            margin-bottom: 16px;
            background: #f9fafb;
            border-radius: 4px;
        }
        .post-item h3 { margin-bottom: 8px; color: #333; }
        .post-item .meta {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
        }
        .post-item a {
            color: #306998;
            text-decoration: none;
        }
        .post-item a:hover { text-decoration: underline; }
        .sentiment-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .sentiment-badge.positive { background: #d1fae5; color: #065f46; }
        .sentiment-badge.negative { background: #fee2e2; color: #991b1b; }
        .sentiment-badge.neutral { background: #fef3c7; color: #92400e; }
        .loading {
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐍 PyCon Community Pulse</h1>
            <p>Real-time sentiment analysis of PyCon community discussions</p>
        </div>

        <div class="disclaimer">
            <h3>⚠️ Demo Disclaimer</h3>
            <p><strong>This is a demonstration application for educational purposes only.</strong></p>
            <ul>
                <li>This application analyzes publicly available posts from Dev.to, Medium, YouTube, and GitHub</li>
                <li>AI sentiment analysis is automated and for demonstration purposes - not intended to judge or interpret author intent</li>
                <li>All content remains property of original authors and platforms</li>
                <li>No personal data is collected or stored beyond public post metadata</li>
                <li>Sentiment scores are AI-generated estimates and may not reflect actual author sentiment</li>
            </ul>
        </div>

        <div class="stats" id="stats-container">
            <div class="stat-card">
                <h3 id="total-posts">...</h3>
                <p>Total Posts</p>
            </div>
            <div class="stat-card">
                <h3 id="analyzed-posts">...</h3>
                <p>Analyzed</p>
            </div>
            <div class="stat-card">
                <h3 id="positive-posts">...</h3>
                <p>Positive</p>
            </div>
        </div>

        <div class="sentiment">
            <h2>📊 Sentiment Overview (Last 7 Days)</h2>
            <div class="sentiment-bar" id="sentiment-bar">
                <div style="flex: 1; background: #e5e7eb; display: flex; align-items: center; justify-content: center; color: #666;">
                    Loading...
                </div>
            </div>
            <div class="sentiment-legend" id="sentiment-legend">
                <span><span class="dot sentiment-positive"></span> Positive: <span id="positive-count">...</span></span>
                <span><span class="dot sentiment-neutral"></span> Neutral: <span id="neutral-count">...</span></span>
                <span><span class="dot sentiment-negative"></span> Negative: <span id="negative-count">...</span></span>
            </div>
        </div>

        <div class="topics">
            <h2>🔥 Trending Topics</h2>
            <div class="topic-cloud" id="topics-content">
                <span class="loading">Loading topics...</span>
            </div>
        </div>

        <div class="posts">
            <h2>📝 Recent Posts</h2>
            <div id="posts-content">
                <p class="loading">Loading recent posts...</p>
            </div>
        </div>
    </div>
"""

    # Start fetching all API data in parallel
    sentiment_task = asyncio.create_task(call_api("/sentiment/stats"))
    topics_task = asyncio.create_task(call_api("/topics/trending?limit=10"))
    posts_task = asyncio.create_task(call_api("/posts?limit=10"))

    # Wait for sentiment data and stream it
    sentiment_data = await sentiment_task
    if sentiment_data:
        total_posts = sentiment_data.get("total_posts", 0)
        analyzed_posts = sentiment_data.get("analyzed_posts", 0)
        positive = sentiment_data.get("positive", 0)
        neutral = sentiment_data.get("neutral", 0)
        negative = sentiment_data.get("negative", 0)
        total_sentiment = positive + neutral + negative

        yield f"""
    <script>
        document.getElementById('total-posts').textContent = '{total_posts}';
        document.getElementById('analyzed-posts').textContent = '{analyzed_posts}';
        document.getElementById('positive-posts').textContent = '{positive}';
        document.getElementById('positive-count').textContent = '{positive}';
        document.getElementById('neutral-count').textContent = '{neutral}';
        document.getElementById('negative-count').textContent = '{negative}';

        var sentimentBar = document.getElementById('sentiment-bar');
        {'sentimentBar.innerHTML = `<div class="sentiment-positive" style="flex: ' + str(positive) + '"></div><div class="sentiment-neutral" style="flex: ' + str(neutral) + '"></div><div class="sentiment-negative" style="flex: ' + str(negative) + '"></div>`;' if total_sentiment > 0 else 'sentimentBar.innerHTML = `<div style="flex: 1; background: #e5e7eb; display: flex; align-items: center; justify-content: center; color: #666;">No data yet</div>`;'}
    </script>
"""

    # Wait for topics and stream them
    topics_data = await topics_task
    if topics_data and "topics" in topics_data and topics_data["topics"]:
        topics_html = "".join([
            f'<span class="topic-tag">{t["topic"]} ({t["count"]})</span>'
            for t in topics_data["topics"]
        ])
        yield f"""
    <script>
        document.getElementById('topics-content').innerHTML = `{topics_html}`;
    </script>
"""
    else:
        yield """
    <script>
        document.getElementById('topics-content').innerHTML = '<p style="color: #666;">No topics extracted yet</p>';
    </script>
"""

    # Wait for posts and stream them
    posts_data = await posts_task
    if posts_data and "posts" in posts_data and posts_data["posts"]:
        posts_html = ""
        for post in posts_data["posts"]:
            title = post.get("title", "No title")
            source = post.get("source", "Unknown")
            url = post.get("url", "#")
            published_at = post.get("published_at")

            date_str = "N/A"
            if published_at:
                try:
                    date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%Y-%m-%d')
                except:
                    pass

            sentiment = post.get("sentiment", "unknown")

            # Escape for JavaScript string
            title = title.replace("'", "\\'").replace('"', '\\"')
            source = source.replace("'", "\\'")
            url = url.replace("'", "\\'")

            posts_html += f'''
                <div class="post-item">
                    <h3>{title}</h3>
                    <div class="meta">
                        <span>{source}</span> •
                        <span>{date_str}</span>
                    </div>
                    <span class="sentiment-badge {sentiment}">{sentiment}</span>
                    <a href="{url}" target="_blank">View original →</a>
                </div>
            '''

        yield f"""
    <script>
        document.getElementById('posts-content').innerHTML = `{posts_html}`;
    </script>
"""
    else:
        yield """
    <script>
        document.getElementById('posts-content').innerHTML = '<p style="color: #666;">No posts collected yet</p>';
    </script>
"""

    # Add auto-refresh script
    yield """
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""


@app.get("/")
async def dashboard() -> StreamingResponse:
    """
    Stream the dashboard page with progressive rendering.

    Uses FastAPI's StreamingResponse to send HTML chunks as data arrives:
    1. Browser receives and renders page shell immediately (<200ms)
    2. API data fetched in parallel on server
    3. Page updates progressively as each API responds
    4. Pure Python/FastAPI - no client-side JavaScript fetching needed

    Returns:
        StreamingResponse: HTML stream with progressive content
    """
    return StreamingResponse(
        stream_dashboard(),
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # Disable nginx buffering for true streaming
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
