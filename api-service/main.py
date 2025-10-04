"""
API Service - Main REST API for PyCon Community Pulse
Provides endpoints for accessing posts, sentiment, and trends
"""
import sys
sys.path.append('..')

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn

from shared import get_db, config, Post, SentimentAnalysis, Topic, Entity
from pydantic import BaseModel

# FastAPI app
app = FastAPI(
    title="PyCon Community Pulse API",
    description="API for accessing PyCon community sentiment and trends",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for responses
class PostResponse(BaseModel):
    id: int
    source: str
    source_url: str
    title: Optional[str]
    content: Optional[str]
    author_name: Optional[str]
    author_url: Optional[str]
    published_at: Optional[datetime]
    collected_at: datetime
    tags: Optional[dict]
    sentiment: Optional[str]
    confidence: Optional[float]

    class Config:
        from_attributes = True


class SentimentStats(BaseModel):
    total_posts: int
    positive: int
    negative: int
    neutral: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    avg_confidence: float


class TrendingTopic(BaseModel):
    topic: str
    count: int
    avg_relevance: float


class EntityStat(BaseModel):
    entity_name: str
    entity_type: str
    mention_count: int


# Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "PyCon Community Pulse API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/posts", response_model=List[PostResponse])
async def get_posts(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get recent posts"""
    query = db.query(Post).outerjoin(SentimentAnalysis)

    if source:
        query = query.filter(Post.source == source)

    posts = query.order_by(desc(Post.published_at)).limit(limit).offset(offset).all()

    return [
        PostResponse(
            id=p.id,
            source=p.source,
            source_url=p.source_url,
            title=p.title,
            content=p.content[:500] if p.content else None,  # Truncate for API
            author_name=p.author_name,
            author_url=p.author_url,
            published_at=p.published_at,
            collected_at=p.collected_at,
            tags=p.tags,
            sentiment=p.sentiment[0].sentiment if p.sentiment else None,
            confidence=float(p.sentiment[0].confidence) if p.sentiment else None
        )
        for p in posts
    ]


@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get specific post by ID"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return PostResponse(
        id=post.id,
        source=post.source,
        source_url=post.source_url,
        title=post.title,
        content=post.content,
        author_name=post.author_name,
        author_url=post.author_url,
        published_at=post.published_at,
        collected_at=post.collected_at,
        tags=post.tags,
        sentiment=post.sentiment[0].sentiment if post.sentiment else None,
        confidence=float(post.sentiment[0].confidence) if post.sentiment else None
    )


@app.get("/sentiment/stats", response_model=SentimentStats)
async def get_sentiment_stats(
    days: int = Query(7, le=90),
    db: Session = Depends(get_db)
):
    """Get overall sentiment statistics"""
    since = datetime.now() - timedelta(days=days)

    # Get all sentiment analysis results
    sentiments = db.query(SentimentAnalysis).join(Post).filter(
        Post.published_at >= since
    ).all()

    if not sentiments:
        return SentimentStats(
            total_posts=0, positive=0, negative=0, neutral=0,
            positive_percentage=0, negative_percentage=0, neutral_percentage=0,
            avg_confidence=0
        )

    total = len(sentiments)
    positive = sum(1 for s in sentiments if s.sentiment == "positive")
    negative = sum(1 for s in sentiments if s.sentiment == "negative")
    neutral = sum(1 for s in sentiments if s.sentiment == "neutral")
    avg_conf = sum(float(s.confidence) for s in sentiments) / total

    return SentimentStats(
        total_posts=total,
        positive=positive,
        negative=negative,
        neutral=neutral,
        positive_percentage=round((positive / total) * 100, 2),
        negative_percentage=round((negative / total) * 100, 2),
        neutral_percentage=round((neutral / total) * 100, 2),
        avg_confidence=round(avg_conf, 4)
    )


@app.get("/trending/topics", response_model=List[TrendingTopic])
async def get_trending_topics(
    limit: int = Query(10, le=50),
    days: int = Query(7, le=90),
    db: Session = Depends(get_db)
):
    """Get trending topics"""
    since = datetime.now() - timedelta(days=days)

    topics = db.query(
        Topic.topic,
        func.count(Topic.id).label("count"),
        func.avg(Topic.relevance_score).label("avg_relevance")
    ).join(Post).filter(
        Post.published_at >= since
    ).group_by(Topic.topic).order_by(desc("count")).limit(limit).all()

    return [
        TrendingTopic(
            topic=t.topic,
            count=t.count,
            avg_relevance=round(float(t.avg_relevance), 4)
        )
        for t in topics
    ]


@app.get("/trending/entities", response_model=List[EntityStat])
async def get_trending_entities(
    limit: int = Query(10, le=50),
    entity_type: Optional[str] = None,
    days: int = Query(7, le=90),
    db: Session = Depends(get_db)
):
    """Get trending entities (people, talks, libraries)"""
    since = datetime.now() - timedelta(days=days)

    query = db.query(
        Entity.entity_name,
        Entity.entity_type,
        func.sum(Entity.mention_count).label("total_mentions")
    ).join(Post).filter(Post.published_at >= since)

    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)

    entities = query.group_by(
        Entity.entity_name, Entity.entity_type
    ).order_by(desc("total_mentions")).limit(limit).all()

    return [
        EntityStat(
            entity_name=e.entity_name,
            entity_type=e.entity_type,
            mention_count=e.total_mentions
        )
        for e in entities
    ]


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics"""
    total_posts = db.query(func.count(Post.id)).scalar()
    analyzed_posts = db.query(func.count(Post.id)).filter(Post.analyzed == True).scalar()
    sources = db.query(Post.source, func.count(Post.id)).group_by(Post.source).all()

    return {
        "total_posts": total_posts,
        "analyzed_posts": analyzed_posts,
        "pending_analysis": total_posts - analyzed_posts,
        "sources": {source: count for source, count in sources}
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )
