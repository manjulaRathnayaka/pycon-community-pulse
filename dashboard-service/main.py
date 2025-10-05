"""
Dashboard Service - Web UI for PyCon Community Pulse
Displays sentiment trends, popular topics, and posts
"""
import sys
import os

# Add current directory to path to import shared module
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
import uvicorn

from shared import get_db, config, Post, SentimentAnalysis, Topic

app = FastAPI(
    title="PyCon Community Pulse - Dashboard",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard page"""

    # Get stats
    total_posts = db.query(func.count(Post.id)).scalar()
    analyzed_posts = db.query(func.count(Post.id)).filter(Post.analyzed == True).scalar()

    # Get sentiment stats (last 7 days)
    since = datetime.now() - timedelta(days=7)
    sentiments = db.query(SentimentAnalysis).join(Post).filter(
        Post.published_at >= since
    ).all()

    sentiment_stats = {
        "positive": sum(1 for s in sentiments if s.sentiment == "positive"),
        "negative": sum(1 for s in sentiments if s.sentiment == "negative"),
        "neutral": sum(1 for s in sentiments if s.sentiment == "neutral"),
    }

    # Get trending topics
    topics = db.query(
        Topic.topic,
        func.count(Topic.id).label("count")
    ).join(Post).filter(
        Post.published_at >= since
    ).group_by(Topic.topic).order_by(desc("count")).limit(10).all()

    # Get recent posts
    recent_posts = db.query(Post).outerjoin(SentimentAnalysis).order_by(
        desc(Post.published_at)
    ).limit(10).all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "total_posts": total_posts,
            "analyzed_posts": analyzed_posts,
            "sentiment_stats": sentiment_stats,
            "topics": [{"topic": t.topic, "count": t.count} for t in topics],
            "recent_posts": [
                {
                    "title": p.title or "No title",
                    "source": p.source,
                    "author": p.author_name,
                    "url": p.source_url,
                    "sentiment": p.sentiment[0].sentiment if p.sentiment else "unknown",
                    "published_at": p.published_at
                }
                for p in recent_posts
            ]
        }
    )


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "Dashboard"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
