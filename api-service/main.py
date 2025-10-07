"""
API Service - Main REST API for PyCon Community Pulse.

This service provides RESTful endpoints for accessing posts, sentiment analysis,
and trending topics. It automatically triggers AI analysis when needed.
"""
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

# Add current directory to path to import db module
sys.path.insert(0, os.path.dirname(__file__))

from db import get_db, get_db_context, init_db, config, Post, SentimentAnalysis, Topic

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AI Analysis Service URL (Choreo auto-injects from connection: connection-ai-analysis)
AI_SERVICE_URL = os.getenv("CHOREO_CONNECTION_AI_ANALYSIS_SERVICEURL", "http://localhost:8001")

# FastAPI app
app = FastAPI(
    title="PyCon Community Pulse API",
    description="REST API for accessing posts, sentiment stats, and trends",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Flag to track if DB is initialized
_db_initialized = False


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database tables on startup."""
    global _db_initialized
    try:
        init_db()
        logger.info("Database tables initialized successfully")
        _db_initialized = True
    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)


# Response Models
class PostResponse(BaseModel):
    """Response model for a single post."""
    id: int
    source: str
    title: Optional[str]
    author: Optional[str]
    url: str
    published_at: Optional[datetime]
    analyzed: bool

    class Config:
        from_attributes = True


class PostsListResponse(BaseModel):
    """Response model for list of posts."""
    posts: List[PostResponse]
    count: int


class SentimentStatsResponse(BaseModel):
    """Response model for sentiment statistics."""
    total_posts: int = Field(..., description="Total number of posts collected")
    analyzed_posts: int = Field(..., description="Number of posts analyzed")
    positive: int = Field(..., description="Number of positive posts")
    negative: int = Field(..., description="Number of negative posts")
    neutral: int = Field(..., description="Number of neutral posts")
    average_sentiment: float = Field(..., description="Average sentiment score")


class TopicItem(BaseModel):
    """Response model for a single topic."""
    topic: str
    count: int


class TrendingTopicsResponse(BaseModel):
    """Response model for trending topics."""
    topics: List[TopicItem]
    count: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    service: str
    database: str
    error: Optional[str] = None


@app.get("/", response_model=dict)
async def root() -> dict:
    """
    Root endpoint providing service information.

    Returns:
        dict: Service name, status, and version
    """
    return {
        "service": "PyCon Community Pulse API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint for monitoring.

    Args:
        db: Database session from dependency injection

    Returns:
        HealthResponse: Current health status

    Raises:
        HTTPException: If database connection fails
    """
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(
            status="healthy",
            service="api-service",
            database="connected"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "degraded",
                "service": "api-service",
                "database": "error",
                "error": str(e)
            }
        )


@app.get("/posts", response_model=PostsListResponse)
async def get_posts(
    limit: int = Query(20, ge=1, le=100, description="Number of posts to return"),
    db: Session = Depends(get_db)
) -> PostsListResponse:
    """
    Get recent posts ordered by publication date.

    Args:
        limit: Maximum number of posts to return (1-100)
        db: Database session from dependency injection

    Returns:
        PostsListResponse: List of posts and count

    Raises:
        HTTPException: If database query fails
    """
    try:
        posts = db.query(Post).order_by(desc(Post.published_at)).limit(limit).all()

        post_responses = [
            PostResponse(
                id=p.id,
                source=p.source,
                title=p.title,
                author=p.author_name,
                url=p.source_url,
                published_at=p.published_at,
                analyzed=p.analyzed
            )
            for p in posts
        ]

        return PostsListResponse(posts=post_responses, count=len(post_responses))
    except Exception as e:
        logger.error(f"Error fetching posts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching posts: {str(e)}")


async def trigger_ai_analysis_if_needed(db: Session, min_analyzed: int = 10) -> None:
    """
    Trigger AI analysis if we don't have enough analyzed posts.

    This function checks if the number of analyzed posts is below a threshold
    and triggers background AI analysis for pending posts if needed.

    Args:
        db: Database session
        min_analyzed: Minimum number of analyzed posts before triggering (default: 10)
    """
    try:
        analyzed_count = db.query(func.count(Post.id)).filter(Post.analyzed == True).scalar() or 0

        # If we have fewer than min_analyzed posts, trigger analysis
        if analyzed_count < min_analyzed:
            pending_count = db.query(func.count(Post.id)).filter(Post.analyzed == False).scalar() or 0

            if pending_count > 0:
                # Trigger AI analysis for pending posts (limit to avoid excessive costs)
                limit = min(20, pending_count)  # Max 20 posts per trigger
                logger.info(f"Triggering AI analysis for {limit} pending posts...")

                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        response = await client.post(
                            f"{AI_SERVICE_URL.rstrip('/')}/analyze/pending",
                            params={"limit": limit}
                        )
                        logger.info(f"AI analysis triggered: {response.status_code}")
                except httpx.TimeoutException:
                    logger.info("AI analysis triggered (timeout expected - processing in background)")
                except Exception as e:
                    logger.warning(f"AI analysis trigger failed: {e}")
    except Exception as e:
        logger.error(f"Error checking analysis status: {e}", exc_info=True)


@app.get("/sentiment/stats", response_model=SentimentStatsResponse)
async def get_sentiment_stats(db: Session = Depends(get_db)) -> SentimentStatsResponse:
    """
    Get sentiment statistics for all analyzed posts.

    Automatically triggers AI analysis if not enough posts are analyzed.

    Args:
        db: Database session from dependency injection

    Returns:
        SentimentStatsResponse: Aggregated sentiment statistics

    Raises:
        HTTPException: If database query fails
    """
    try:
        # Trigger AI analysis if needed (on-demand)
        await trigger_ai_analysis_if_needed(db, min_analyzed=10)

        total_posts = db.query(func.count(Post.id)).scalar() or 0

        # Get sentiment counts
        sentiments = db.query(SentimentAnalysis).all()
        positive = sum(1 for s in sentiments if s.sentiment == "positive")
        negative = sum(1 for s in sentiments if s.sentiment == "negative")
        neutral = sum(1 for s in sentiments if s.sentiment == "neutral")

        # Calculate average sentiment score
        avg_sentiment = 0.0
        if sentiments:
            avg_sentiment = sum(
                float(s.positive_score or 0) - float(s.negative_score or 0)
                for s in sentiments
            ) / len(sentiments)

        return SentimentStatsResponse(
            total_posts=total_posts,
            analyzed_posts=len(sentiments),
            positive=positive,
            negative=negative,
            neutral=neutral,
            average_sentiment=round(avg_sentiment, 2)
        )
    except Exception as e:
        logger.error(f"Error fetching sentiment stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching sentiment stats: {str(e)}")


@app.get("/topics/trending", response_model=TrendingTopicsResponse)
async def get_trending_topics(
    limit: int = Query(10, ge=1, le=50, description="Number of topics to return"),
    db: Session = Depends(get_db)
) -> TrendingTopicsResponse:
    """
    Get trending topics across all analyzed posts.

    Args:
        limit: Maximum number of topics to return (1-50)
        db: Database session from dependency injection

    Returns:
        TrendingTopicsResponse: List of topics with their counts

    Raises:
        HTTPException: If database query fails
    """
    try:
        topics = db.query(
            Topic.topic,
            func.count(Topic.id).label("count")
        ).group_by(Topic.topic).order_by(desc("count")).limit(limit).all()

        topic_items = [TopicItem(topic=t.topic, count=t.count) for t in topics]

        return TrendingTopicsResponse(topics=topic_items, count=len(topic_items))
    except Exception as e:
        logger.error(f"Error fetching trending topics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching trending topics: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting API service on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=config.LOG_LEVEL.lower(),
        reload=False  # Disable reload in production
    )
